"""FastAPI backend — 包装 Agent 为 SSE 流式 API。

接口:
  POST /chat   — 流式输出 Agent 推理过程(tool_call / tool_result / text)
  GET  /health — 健康检查
"""

from __future__ import annotations

import json
import os
import smtplib
import sys
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Iterable

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from pydantic import BaseModel

# 确保 backend/ 目录里 agent.py 能被导入
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import (  # noqa: E402
    save_conversation, list_conversations, delete_conversation,
    log_usage, get_usage_stats,
)

# 离线模式 — 防止 huggingface_hub 联网检查超时
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

from agent import build_agent  # noqa: E402


# 用于反馈持久化
ROOT = Path(__file__).resolve().parent.parent
FEEDBACK_FILE = ROOT / "data" / "feedback.jsonl"


app = FastAPI(title="检测行业 Agent")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 启动时构建 Agent(只构建一次,避免每次请求重新加载模型)
agent = None


@app.on_event("startup")
def startup():
    global agent
    print("[*] 启动时构建 Agent ...")
    agent = build_agent()
    print("[OK] Agent 就绪")


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]


@app.get("/health")
def health():
    return {"ok": True, "agent_ready": agent is not None}


def _serialize_tool_call(tc: dict[str, Any]) -> dict:
    return {
        "type": "tool_call",
        "name": tc.get("name", ""),
        "args": tc.get("args", {}),
    }


def _serialize_tool_result(content: str) -> dict:
    # 工具结果可能很长,截断到 1500 字防止前端炸
    if isinstance(content, str) and len(content) > 1500:
        content = content[:1500] + "..."
    return {"type": "tool_result", "content": content}


def _sse(data: dict) -> str:
    """SSE 格式"""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def stream_agent(messages_payload: list[tuple[str, str]]) -> Iterable[str]:
    """跑 Agent,把每个 step 转成 SSE 事件 yield 出去"""
    yield _sse({"type": "start"})

    try:
        for chunk in agent.stream({"messages": messages_payload}, stream_mode="updates"):
            for node, state in chunk.items():
                msgs = state.get("messages", []) if isinstance(state, dict) else []
                if not msgs:
                    continue
                msg = msgs[-1]

                # LLM 节点(agent / model / tools 的反向): 检查是否有 tool_calls
                tool_calls = getattr(msg, "tool_calls", None)
                if tool_calls:
                    for tc in tool_calls:
                        yield _sse(_serialize_tool_call(tc))
                    continue

                # 工具节点: 工具调用结果
                if node == "tools":
                    yield _sse(_serialize_tool_result(getattr(msg, "content", "")))
                    continue

                # Agent 的最终文本输出
                content = getattr(msg, "content", "")
                if content:
                    yield _sse({"type": "text", "content": content})

    except Exception as e:
        yield _sse({"type": "error", "message": str(e)})

    yield _sse({"type": "done"})


@app.post("/chat")
def chat(req: ChatRequest):
    if agent is None:
        raise HTTPException(503, "Agent 未就绪")

    if not req.messages:
        raise HTTPException(400, "messages 不能为空")

    if req.messages[-1].role != "user":
        raise HTTPException(400, "最后一条 message 必须是 user")

    # 转成 LangGraph 期望的格式: [(role, content), ...]
    payload = [(m.role, m.content) for m in req.messages]
    question = req.messages[-1].content[:300]

    def logged_stream():
        tools_called = []
        for chunk in stream_agent(payload):
            # 收集工具调用记录
            if '"type":"tool_call"' in chunk:
                import re
                m = re.search(r'"name":"([^"]+)"', chunk)
                if m:
                    tools_called.append(m.group(1))
            yield chunk
        # 异步记录用量
        try:
            log_usage(question, tools_called, 0)
        except Exception:
            pass

    return StreamingResponse(
        logged_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ============== File Upload ==============

def is_image(ext: str) -> bool:
    return ext in (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp")


def extract_text(file_path: str, filename: str) -> str:
    """提取文件文字内容"""
    ext = os.path.splitext(filename)[1].lower()

    if ext in (".txt", ".md", ".json", ".csv", ".py", ".js", ".ts", ".tsx", ".jsx", ".html", ".css", ".xml", ".yaml", ".yml", ".log"):
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    if ext == ".pdf":
        try:
            import fitz  # pymupdf
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except ImportError:
            return "[PDF 解析库未安装]"

    if ext in (".docx", ".doc"):
        try:
            from docx import Document
            doc = Document(file_path)
            return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except ImportError:
            return "[Word 解析库未安装]"

    if ext in (".xlsx", ".xls"):
        try:
            import openpyxl
            wb = openpyxl.load_workbook(file_path, data_only=True)
            text = ""
            for sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
                text += f"\n--- Sheet: {sheet_name} ---\n"
                for row in ws.iter_rows(values_only=True):
                    row_text = "\t".join(str(c) if c is not None else "" for c in row)
                    if row_text.strip():
                        text += row_text + "\n"
                if len(text) > 50000:
                    text = text[:50000] + "\n... (文件过长,已截断)"
            wb.close()
            return text
        except Exception as e:
            return f"[Excel 解析失败: {e}]"

    if ext in (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"):
        return "[图片文件，请使用 analyze_image 工具分析]"

    return f"[不支持的文件类型: {ext}]"

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """上传文件，提取文字内容返回。图片保存到公开目录并返回URL"""
    if not file.filename:
        raise HTTPException(400, "文件名不能为空")

    ext = os.path.splitext(file.filename)[1].lower()
    allowed = {".txt", ".md", ".pdf", ".docx", ".doc", ".xlsx", ".xls",
               ".json", ".csv", ".py", ".js", ".ts", ".tsx", ".html",
               ".css", ".xml", ".yaml", ".yml", ".log", ".png", ".jpg",
               ".jpeg", ".gif", ".bmp", ".webp"}
    if ext not in allowed:
        raise HTTPException(400, f"不支持的文件类型: {ext}")

    content = await file.read()

    if is_image(ext):
        # 图片保存到 agent 的静态目录，返回可访问 URL
        upload_dir = ROOT / "data" / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        safe_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        img_path = upload_dir / safe_name
        img_path.write_bytes(content)
        # 通过 nginx 的 /inspection/ → backend 路由来访问
        # 加一个专门的静态文件路由
        image_url = f"http://1.15.170.85/inspection/uploads/{safe_name}"
        return {
            "filename": file.filename,
            "ext": ext,
            "text": f"[图片文件] 可通过 analyze_image 工具分析，图片链接: {image_url}",
            "image_url": image_url,
            "length": 0,
        }

    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        text = extract_text(tmp_path, file.filename)
    finally:
        os.unlink(tmp_path)

    return {
        "filename": file.filename,
        "ext": ext,
        "text": text,
        "length": len(text),
    }


# ============== 图片静态服务 ==============
@app.get("/uploads/{filename}")
def serve_upload(filename: str):
    """提供上传图片的公开访问"""
    file_path = ROOT / "data" / "uploads" / filename
    if file_path.exists():
        return FileResponse(file_path)
    raise HTTPException(404, "图片不存在")


# ============== 对话记忆 API ==============

class ConversationSave(BaseModel):
    id: str
    title: str
    messages: list[dict]

@app.post("/conversations")
def save_conv(req: ConversationSave):
    try:
        save_conversation(req.id, req.title, req.messages)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/conversations")
def list_convs():
    return list_conversations()

@app.delete("/conversations/{conv_id}")
def delete_conv(conv_id: str):
    delete_conversation(conv_id)
    return {"ok": True}


# ============== 用量统计 API ==============

@app.get("/admin/stats")
def admin_stats():
    return get_usage_stats()


# ============== Feedback ==============

class FeedbackRequest(BaseModel):
    message: str
    rating: int | None = None  # 1-5 或 None
    name: str | None = None
    related_query: str | None = None  # 用户当时聊的问题(可选上下文)


def _send_feedback_email(entry: dict) -> None:
    """如果配置了 SMTP_* 环境变量,就发邮件;否则 raise(交给调用者忽略)。"""
    host = os.getenv("SMTP_HOST")
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")
    if not (host and user and password):
        raise RuntimeError("SMTP 未配置")

    port = int(os.getenv("SMTP_PORT", "465"))
    to = os.getenv("SMTP_TO", user)

    rating = entry.get("rating")
    rating_str = f"{rating}★" if rating else "无评分"
    name = entry.get("name") or "匿名"

    body_lines = [
        f"时间: {entry['timestamp']}",
        f"评分: {rating_str}",
        f"反馈人: {name}",
        f"相关查询: {entry.get('related_query') or '无'}",
        "",
        "===== 反馈内容 =====",
        entry["message"],
    ]
    body = "\n".join(body_lines)

    msg = MIMEMultipart()
    msg["From"] = user
    msg["To"] = to
    msg["Subject"] = f"[检测Agent反馈] {name} · {rating_str}"
    msg.attach(MIMEText(body, "plain", "utf-8"))

    with smtplib.SMTP_SSL(host, port, timeout=10) as server:
        server.login(user, password)
        server.send_message(msg)


@app.post("/feedback")
def feedback(req: FeedbackRequest):
    msg = (req.message or "").strip()
    if not msg:
        raise HTTPException(400, "反馈内容不能为空")
    if len(msg) > 2000:
        raise HTTPException(400, "反馈内容过长(最多 2000 字)")

    entry = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "message": msg,
        "rating": req.rating,
        "name": (req.name or "").strip() or None,
        "related_query": (req.related_query or "").strip() or None,
    }

    # 1. 永远存本地
    FEEDBACK_FILE.parent.mkdir(exist_ok=True, parents=True)
    with FEEDBACK_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # 2. 尽量发邮件(配了就发,没配就跳过)
    email_status = "skipped"
    email_error = None
    try:
        _send_feedback_email(entry)
        email_status = "sent"
    except RuntimeError:
        # SMTP 未配置,正常情况
        pass
    except Exception as e:
        email_status = "failed"
        email_error = str(e)
        print(f"[WARN] 邮件发送失败: {e}")

    return {
        "ok": True,
        "saved": True,
        "email": email_status,
        "email_error": email_error,
    }


@app.get("/")
def root():
    return JSONResponse({
        "name": "检测行业 Agent API",
        "endpoints": {
            "POST /chat": "Chat with the inspection agent (SSE streaming)",
            "POST /feedback": "Submit user feedback (saved to file + optional email)",
            "GET /health": "Health check",
        },
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
