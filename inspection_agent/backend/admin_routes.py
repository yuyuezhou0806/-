"""管理后台 API：统计、对话记录、反馈查看"""

import json
import os
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel

from database import (
    get_stats, get_recent_conversations, get_conversation_count,
    get_feedback_list, get_feedback_count,
    verify_admin, check_session, create_admin_user,
)

router = APIRouter(prefix="/admin", tags=["admin"])

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "gangzi2026")


class LoginRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


def require_auth(request: Request) -> str:
    """从 header 或 cookie 取 token"""
    token = request.headers.get("X-Admin-Token") or request.cookies.get("admin_token")
    if not token:
        raise HTTPException(401, "请先登录")
    username = check_session(token)
    if not username:
        raise HTTPException(401, "登录已过期，请重新登录")
    return username


# ====== 登录 ======

@router.post("/login")
def login(req: LoginRequest):
    token = verify_admin(req.username, req.password)
    if not token:
        raise HTTPException(401, "用户名或密码错误")
    return {"ok": True, "token": token, "username": req.username}


@router.get("/me")
def me(request: Request):
    user = require_auth(request)
    return {"username": user}


# ====== 统计 ======

@router.get("/stats")
def stats(request: Request, days: int = 30):
    require_auth(request)
    data = get_stats(days)
    data["conversation_count"] = get_conversation_count()
    data["feedback_count"] = get_feedback_count()
    return data


# ====== 对话记录 ======

@router.get("/conversations")
def conversations(request: Request, limit: int = 50, offset: int = 0):
    require_auth(request)
    rows = get_recent_conversations(limit, offset)
    total = get_conversation_count()
    return {"total": total, "items": rows, "limit": limit, "offset": offset}


# ====== 反馈 ======

@router.get("/feedback")
def feedback_list(request: Request, limit: int = 50, offset: int = 0):
    require_auth(request)
    items = get_feedback_list(limit, offset)
    total = get_feedback_count()
    return {"total": total, "items": items, "limit": limit, "offset": offset}


# ====== 密码管理 ======

@router.post("/change-password")
def change_password(req: ChangePasswordRequest, request: Request):
    username = require_auth(request)
    # 老密码验证
    if not verify_admin(username, req.old_password):
        raise HTTPException(400, "原密码错误")
    create_admin_user(username, req.new_password)
    return {"ok": True, "message": "密码已修改"}


# ====== 初始化管理员 ======

@router.post("/setup")
def setup(req: LoginRequest):
    """首次设置管理员账号，仅在没有管理员时可用"""
    conn = __import__("database").get_conn()
    count = conn.execute("SELECT COUNT(*) FROM admin_users").fetchone()[0]
    if count > 0:
        raise HTTPException(400, "管理员已存在，请使用 /admin/login 登录")
    ok = create_admin_user(req.username, req.password)
    if not ok:
        raise HTTPException(400, "创建失败")
    return {"ok": True, "message": "管理员创建成功，请登录"}

# ====== 管理后台页面 ======

@router.get("/panel", response_class=HTMLResponse)
def admin_panel():
    static_dir = Path(__file__).resolve().parent / "static"
    html_path = static_dir / "admin.html"
    if html_path.exists():
        return html_path.read_text(encoding="utf-8")
    return "<h1>管理页面未找到</h1>"
