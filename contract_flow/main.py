from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from database import engine, Base
from models import User
import crud
import schemas
from auth import get_password_hash
from sqlalchemy.orm import Session
from database import SessionLocal
from sqlalchemy import text, inspect

from routers import auth, forms, io


def migrate_db():
    """简单迁移：为已有表添加缺失的列"""
    inspector = inspect(engine)
    columns = [c["name"] for c in inspector.get_columns("contract_forms")]
    if "attachments" not in columns:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE contract_forms ADD COLUMN attachments TEXT DEFAULT '[]'"))
            conn.commit()
            print("[migrate] 已添加 attachments 列")
    if "project_manager_name" not in columns:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE contract_forms ADD COLUMN project_manager_name VARCHAR"))
            conn.commit()
            print("[migrate] 已添加 project_manager_name 列")
    if "estimated_revenue" not in columns:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE contract_forms ADD COLUMN estimated_revenue FLOAT DEFAULT 0"))
            conn.commit()
            print("[migrate] 已添加 estimated_revenue 列")


def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # 初始化默认账号
        default_users = [
            ("admin", "管理员", "admin", "admin123"),
            ("chengjie", "项目承接人", "project_taker", "123456"),
            ("fuze", "项目负责人", "project_manager", "123456"),
            ("bumen", "部门负责人", "dept_head", "123456"),
            ("yingxiao", "营销管理", "marketing", "123456"),
            ("jishu", "技术质量", "tech_quality", "123456"),
        ]
        for username, real_name, role, pwd in default_users:
            existing = db.query(User).filter(User.username == username).first()
            if not existing:
                db.add(User(
                    username=username,
                    real_name=real_name,
                    role=role,
                    hashed_password=get_password_hash(pwd)
                ))
        db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    migrate_db()
    init_db()
    yield


app = FastAPI(title="合同流转确认单系统", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(forms.router)
app.include_router(io.router)

static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

uploads_dir = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")
