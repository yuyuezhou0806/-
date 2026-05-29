"""合同生成器 Web 后端

POST /generate: 上传项目网页截图 → OCR → 提取字段 → 填充 Word 合同模板 → 返回 .doc 下载
GET /: 返回前端单页 HTML
GET /health: 健康检查
"""

import json
import re
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

import ocr_engine
import business


BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"
TEMPLATE_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

for d in (UPLOAD_DIR, OUTPUT_DIR, TEMPLATE_DIR, STATIC_DIR):
    d.mkdir(exist_ok=True, parents=True)


def find_templates():
    """扫描 templates 目录,返回 [(显示名, 文件路径), ...]"""
    templates = []
    # 优先 .docx,再 .doc
    for ext in (".docx", ".doc"):
        for p in sorted(TEMPLATE_DIR.glob(f"*{ext}")):
            # 从文件名提取类型名,如"空白合同【房建】（2021版）.docx" → "房建"
            name = p.stem
            m = re.search(r'[【\[](.+?)[】\]]', name)
            if m:
                display = m.group(1)
            else:
                display = name
            templates.append((display, p))
    return templates


TEMPLATES = find_templates()
if not TEMPLATES:
    print(f"[WARN] 找不到合同模板,请放到 {TEMPLATE_DIR} 下")


app = FastAPI(title="合同生成器")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def safe_name(s: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', "_", s)[:80] or "合同"


@app.get("/", response_class=HTMLResponse)
def index():
    p = STATIC_DIR / "index.html"
    if not p.exists():
        return HTMLResponse("<h1>前端 index.html 缺失</h1>", status_code=500)
    return HTMLResponse(p.read_text(encoding="utf-8"))


@app.get("/health")
def health():
    return {
        "ok": True,
        "templates": [name for name, _ in TEMPLATES],
        "ocr_loaded": ocr_engine._ocr is not None,
    }


@app.get("/templates")
def list_templates():
    """返回可用模板列表"""
    return [
        {"name": name, "file": path.name}
        for name, path in TEMPLATES
    ]


@app.post("/generate")
def generate(file: UploadFile = File(...), template: str = Form(""), check_type: str = Form("")):
    """主接口:上传图 → OCR → 提取字段 → 填合同 → 返回 .docx
    template: 模板显示名(如"房建"),不传则使用第一个模板
    check_type: 检测类别,逗号分隔,如"验收检测,平行检测"
    """
    # 选择模板
    template_path = None
    if template:
        for name, path in TEMPLATES:
            if name == template or path.name == template:
                template_path = path
                break
    if template_path is None:
        # 未指定或找不到,使用第一个
        if not TEMPLATES:
            raise HTTPException(500, "找不到合同模板,请检查 templates 目录")
        template_path = TEMPLATES[0][1]

    if not template_path.exists():
        raise HTTPException(500, f"模板文件不存在: {template_path}")

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, f"请上传图片文件 (当前类型: {file.content_type})")

    t0 = time.time()
    upload_id = uuid.uuid4().hex[:8]
    ext = Path(file.filename or "upload.png").suffix or ".png"
    upload_path = UPLOAD_DIR / f"{upload_id}{ext}"
    upload_path.write_bytes(file.file.read())

    # OCR
    try:
        full_text, texts = ocr_engine.ocr_image(str(upload_path))
    except Exception as e:
        raise HTTPException(500, f"OCR 失败: {e}")
    t_ocr = time.time() - t0

    if not full_text.strip():
        raise HTTPException(422, "图片中未识别到任何文字,请确认截图是清晰的网页内容")

    # 提取字段
    fields = business.extract_fields(full_text)
    if not fields:
        # 返回 OCR 结果让前端展示,帮助用户判断为啥提取不到
        return JSONResponse(
            {
                "ok": False,
                "error": "未提取到关键字段,可能截图不是上海市建设工程项目信息报送系统的页面",
                "ocr_lines": texts[:50],
                "ocr_time_sec": round(t_ocr, 2),
            },
            status_code=422,
        )

    # 构造合同配置 + 填充
    project_name = fields.get("工程名称", "合同")
    output_name = f"{safe_name(project_name)}.docx"

    try:
        config = business.build_contract_config(fields, str(template_path), output_name, check_type)
        business.fill_contract(config)
    except Exception as e:
        raise HTTPException(500, f"填充 Word 合同失败: {e}")

    # fill_contract 把输出放在 template_dir / output_name,move 到 outputs/
    src_path = template_path.parent / output_name
    if not src_path.exists():
        raise HTTPException(500, f"合同生成完成,但找不到输出文件 {src_path}")

    dst_path = OUTPUT_DIR / f"{upload_id}_{output_name}"
    src_path.replace(dst_path)

    elapsed = round(time.time() - t0, 2)

    # 把识别到的字段和OCR原文塞到 header 给前端展示
    # ensure_ascii=True 把中文转 \uXXXX 转义,避免 HTTP header 的 latin-1 限制
    ocr_lines = texts[:80]  # 限制行数避免 header 过大
    return FileResponse(
        path=str(dst_path),
        filename=output_name,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "X-Fields": json.dumps(fields, ensure_ascii=True),
            "X-Elapsed-Sec": str(elapsed),
            "X-OCR-Sec": str(round(t_ocr, 2)),
            "X-OCR-Lines": json.dumps(ocr_lines, ensure_ascii=True),
            "Access-Control-Expose-Headers": "X-Fields, X-Elapsed-Sec, X-OCR-Sec, X-OCR-Lines, Content-Disposition",
        },
    )


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
