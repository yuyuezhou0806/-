"""
IDI 缺陷速查 - 用户认证后端
FastAPI + SQLite + JWT
"""

import os
import sqlite3
import hashlib
import hmac
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

try:
    from jose import jwt, JWTError
    HAS_JOSE = True
except ImportError:
    HAS_JOSE = False

# ========== 配置 ==========
DB_PATH = Path(__file__).parent / "users.db"
WEB_DIR = Path(__file__).parent / "web"
SECRET_KEY = "idi-defects-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

# ========== 数据库 ==========
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# ========== 密码工具 ==========
def hash_password(password: str) -> str:
    """简单密码哈希 (生产环境建议用 bcrypt)"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    return hmac.compare_digest(hash_password(password), password_hash)

# ========== JWT 工具 ==========
def create_access_token(data: dict, expires_delta: timedelta = None):
    if not HAS_JOSE:
        # fallback: 不用 JWT，用简单 token
        return hashlib.sha256(f"{data['sub']}{SECRET_KEY}".encode()).hexdigest()[:32]
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> str:
    """返回 username 或 None"""
    if not HAS_JOSE:
        # fallback 模式下无法真正验证，信任传入的 token
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None

# ========== Pydantic 模型 ==========
REGISTER_CODE = "zchidi"  # 注册密令

class UserRegister(BaseModel):
    username: str
    password: str
    remember: bool = False  # 记住我
    code: str = ""  # 注册密令

class UserLogin(BaseModel):
    username: str
    password: str
    remember: bool = False  # 记住我

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

# ========== FastAPI 应用 ==========
app = FastAPI(title="IDI 缺陷速查认证服务")
security = HTTPBearer(auto_error=False)

# 挂载静态文件（defects.json 需要认证，所以不直接挂整个目录）
@app.on_event("startup")
def startup():
    init_db()

# ========== API 路由 ==========
@app.post("/api/auth/register", response_model=TokenResponse)
def register(body: UserRegister):
    """用户注册"""
    if len(body.username) < 3 or len(body.username) > 20:
        raise HTTPException(status_code=400, detail="用户名长度3-20位")
    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="密码至少6位")
    if body.code != REGISTER_CODE:
        raise HTTPException(status_code=400, detail="注册密令错误")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
            (body.username, hash_password(body.password), datetime.now().isoformat())
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="用户名已存在")
    finally:
        conn.close()

    expire_days = 365 if body.remember else 7
    token = create_access_token({"sub": body.username}, expires_delta=timedelta(days=expire_days))
    return {"access_token": token, "token_type": "bearer"}

@app.post("/api/auth/login", response_model=TokenResponse)
def login(body: UserLogin):
    """用户登录"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT password_hash FROM users WHERE username = ?", (body.username,))
    row = c.fetchone()
    conn.close()

    if not row or not verify_password(body.password, row[0]):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    expire_days = 365 if body.remember else 7
    token = create_access_token({"sub": body.username}, expires_delta=timedelta(days=expire_days))
    return {"access_token": token, "token_type": "bearer"}

@app.get("/api/auth/me")
def me(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """获取当前用户信息"""
    if not credentials:
        raise HTTPException(status_code=401, detail="未登录")
    username = decode_token(credentials.credentials)
    if not username:
        raise HTTPException(status_code=401, detail="登录已过期")
    return {"username": username}

# ========== 受保护的静态资源 ==========
@app.get("/defects.json")
def get_defects(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """ defects.json 需要登录才能访问 """
    if not credentials:
        raise HTTPException(status_code=401, detail="未登录")
    username = decode_token(credentials.credentials)
    if not username:
        raise HTTPException(status_code=401, detail="登录已过期")

    defects_path = WEB_DIR / "defects.json"
    if not defects_path.exists():
        raise HTTPException(status_code=404, detail="数据文件不存在")
    return FileResponse(defects_path)

# ========== 公开静态资源 ==========
@app.get("/", response_class=HTMLResponse)
def index():
    """首页（登录页面）"""
    index_path = WEB_DIR / "index.html"
    if index_path.exists():
        return index_path.read_text(encoding="utf-8")
    raise HTTPException(status_code=404)

@app.get("/imgs/{filename}")
def img_file(filename: str):
    """图片文件"""
    file_path = WEB_DIR / "imgs" / filename
    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)
    raise HTTPException(status_code=404)

@app.get("/{filename}")
def static_file(filename: str):
    """其他静态文件（JS、CSS等）"""
    file_path = WEB_DIR / filename
    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)
    raise HTTPException(status_code=404)

# ========== 启动 ==========
if __name__ == "__main__":
    import uvicorn
    init_db()
    uvicorn.run(app, host="0.0.0.0", port=5173)
