"""
IDI 缺陷速查 - 用户认证后端
FastAPI + SQLite + JWT
"""

import os
import sqlite3
import hashlib
import hmac
import json
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
            is_admin INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)
    # 迁移：添加 is_admin 字段（如果不存在）
    try:
        c.execute("SELECT is_admin FROM users LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
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

# ========== 管理员依赖 ==========
from fastapi import UploadFile, File

def get_current_username(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="未登录")
    username = decode_token(credentials.credentials)
    if not username:
        raise HTTPException(status_code=401, detail="登录已过期")
    return username

def require_admin(username: str = Depends(get_current_username)):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT is_admin FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    if not row or not row[0]:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return username

# ========== 用户管理 API ==========
@app.get("/api/admin/check")
def admin_check(username: str = Depends(get_current_username)):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT is_admin FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    return {"is_admin": bool(row and row[0]), "username": username}

@app.get("/api/admin/users")
def admin_list_users(admin: str = Depends(require_admin)):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, username, is_admin, created_at FROM users ORDER BY id")
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "username": r[1], "is_admin": bool(r[2]), "created_at": r[3]} for r in rows]

class CreateUserBody(BaseModel):
    username: str
    password: str
    is_admin: bool = False

@app.post("/api/admin/users")
def admin_create_user(body: CreateUserBody, admin: str = Depends(require_admin)):
    if len(body.username) < 3 or len(body.username) > 20:
        raise HTTPException(status_code=400, detail="用户名长度3-20位")
    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="密码至少6位")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO users (username, password_hash, is_admin, created_at) VALUES (?, ?, ?, ?)",
            (body.username, hash_password(body.password), 1 if body.is_admin else 0, datetime.now().isoformat())
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="用户名已存在")
    finally:
        conn.close()
    return {"ok": True}

@app.delete("/api/admin/users/{username}")
def admin_delete_user(username: str, admin: str = Depends(require_admin)):
    if username == admin:
        raise HTTPException(status_code=400, detail="不能删除自己")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE username = ?", (username,))
    deleted = c.rowcount
    conn.commit()
    conn.close()
    if deleted == 0:
        raise HTTPException(status_code=404, detail="用户不存在")
    return {"ok": True}

class ResetPasswordBody(BaseModel):
    new_password: str

@app.post("/api/admin/users/{username}/reset")
def admin_reset_password(username: str, body: ResetPasswordBody, admin: str = Depends(require_admin)):
    if len(body.new_password) < 6:
        raise HTTPException(status_code=400, detail="密码至少6位")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET password_hash = ? WHERE username = ?", (hash_password(body.new_password), username))
    updated = c.rowcount
    conn.commit()
    conn.close()
    if updated == 0:
        raise HTTPException(status_code=404, detail="用户不存在")
    return {"ok": True}

@app.post("/api/admin/users/{username}/toggle-admin")
def admin_toggle_admin(username: str, admin: str = Depends(require_admin)):
    if username == admin:
        raise HTTPException(status_code=400, detail="不能修改自己的权限")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT is_admin FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="用户不存在")
    new_val = 0 if row[0] else 1
    c.execute("UPDATE users SET is_admin = ? WHERE username = ?", (new_val, username))
    conn.commit()
    conn.close()
    return {"ok": True, "is_admin": bool(new_val)}

# ========== 缺陷条目管理 API ==========
@app.get("/api/admin/defects")
def admin_list_defects(
    q: str = "",
    period: str = "",
    major: str = "",
    page: int = 1,
    pageSize: int = 50,
    admin: str = Depends(require_admin)
):
    defects_path = WEB_DIR / "defects.json"
    if not defects_path.exists():
        raise HTTPException(status_code=404, detail="数据文件不存在")
    with open(defects_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 筛选
    if q:
        q_lower = q.lower()
        data = [d for d in data if q_lower in d.get("problem", "").lower() or q_lower in d.get("suggestion", "").lower()]
    if period:
        data = [d for d in data if d.get("category_period") == period]
    if major:
        data = [d for d in data if d.get("category_major") == major]

    total = len(data)
    start = (page - 1) * pageSize
    end = start + pageSize
    return {"total": total, "page": page, "pageSize": pageSize, "items": data[start:end]}

@app.get("/api/admin/defects/{global_id}")
def admin_get_defect(global_id: str, admin: str = Depends(require_admin)):
    defects_path = WEB_DIR / "defects.json"
    with open(defects_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    for d in data:
        if d.get("global_id") == global_id:
            return d
    raise HTTPException(status_code=404, detail="缺陷不存在")

class DefectBody(BaseModel):
    category_period: str
    category_major: str
    category_minor: str
    problem: str
    suggestion: str
    image: str = ""

@app.put("/api/admin/defects/{global_id}")
def admin_update_defect(global_id: str, body: DefectBody, admin: str = Depends(require_admin)):
    defects_path = WEB_DIR / "defects.json"
    with open(defects_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    found = False
    for d in data:
        if d.get("global_id") == global_id:
            d["category_period"] = body.category_period
            d["category_major"] = body.category_major
            d["category_minor"] = body.category_minor
            d["problem"] = body.problem
            d["suggestion"] = body.suggestion
            if body.image:
                d["image"] = body.image
            elif "image" in d:
                del d["image"]
            found = True
            break

    if not found:
        raise HTTPException(status_code=404, detail="缺陷不存在")

    with open(defects_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return {"ok": True}

@app.post("/api/admin/defects")
def admin_create_defect(body: DefectBody, admin: str = Depends(require_admin)):
    defects_path = WEB_DIR / "defects.json"
    with open(defects_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 生成新ID
    max_id = 0
    for d in data:
        try:
            gid = int(d.get("global_id", "D0000")[1:])
            max_id = max(max_id, gid)
        except:
            pass

    new_id = max_id + 1
    new_defect = {
        "category_period": body.category_period,
        "category_major": body.category_major,
        "category_minor": body.category_minor,
        "seq": str(new_id),
        "problem": body.problem,
        "suggestion": body.suggestion,
        "global_id": f"D{new_id:04d}",
    }
    if body.image:
        new_defect["image"] = body.image

    data.append(new_defect)

    with open(defects_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return {"ok": True, "global_id": new_defect["global_id"]}

@app.delete("/api/admin/defects/{global_id}")
def admin_delete_defect(global_id: str, admin: str = Depends(require_admin)):
    defects_path = WEB_DIR / "defects.json"
    with open(defects_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    original_len = len(data)
    data = [d for d in data if d.get("global_id") != global_id]

    if len(data) == original_len:
        raise HTTPException(status_code=404, detail="缺陷不存在")

    # 删除对应图片
    img_path = WEB_DIR / "imgs" / f"{global_id}.jpg"
    if img_path.exists():
        img_path.unlink()

    with open(defects_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return {"ok": True}

# ========== 图片上传 API ==========
@app.post("/api/admin/upload")
async def admin_upload_image(
    file: UploadFile = File(...),
    admin: str = Depends(require_admin)
):
    import shutil
    from PIL import Image

    # 保存临时文件
    temp_path = WEB_DIR / "imgs" / file.filename
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 压缩图片
    try:
        img = Image.open(temp_path)
        img.thumbnail((800, 600), Image.LANCZOS)
        base = os.path.splitext(file.filename)[0]
        jpg_path = WEB_DIR / "imgs" / f"{base}.jpg"
        img = img.convert("RGB")
        img.save(jpg_path, "JPEG", quality=80, optimize=True)
        if str(temp_path) != str(jpg_path):
            temp_path.unlink()
        return {"ok": True, "filename": f"{base}.jpg"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ========== admin.html 路由 ==========
@app.get("/admin", response_class=HTMLResponse)
def admin_page():
    admin_path = WEB_DIR / "admin.html"
    if admin_path.exists():
        return admin_path.read_text(encoding="utf-8")
    raise HTTPException(status_code=404)

@app.get("/admin.html", response_class=HTMLResponse)
def admin_page_html():
    return admin_page()

# ========== 启动 ==========
if __name__ == "__main__":
    import uvicorn
    init_db()
    uvicorn.run(app, host="0.0.0.0", port=5173)

