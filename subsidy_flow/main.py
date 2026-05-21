from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from database import engine, Base
from models import User
from auth import get_password_hash
from sqlalchemy.orm import Session
from database import SessionLocal

from routers import auth, public, clients, projects, expenses, reports


def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        default_users = [
            ("admin", "管理员", "admin", "admin123"),
            ("agent", "申报专员", "agent", "agent123"),
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
    init_db()
    yield


app = FastAPI(title="广州市中小企业数字化转型补贴申报管理系统", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(public.router)
app.include_router(clients.router)
app.include_router(projects.router)
app.include_router(expenses.router)
app.include_router(reports.router)

static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

uploads_dir = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")
