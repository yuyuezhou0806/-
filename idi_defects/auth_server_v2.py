"""
IDI 缺陷速查 - 用户认证后端 (工业级 v2)
FastAPI + SQLite(WAL) + JWT + bcrypt + 登录锁定
"""

import os
import sqlite3
import hashlib
import hmac
import json
import base64
import re
from datetime import datetime, timedelta
from pathlib import Path
from functools import wraps

from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

# bcrypt
try:
    import bcrypt
    HAS_BCRYPT = True
except ImportError:
    HAS_BCRYPT = False
    print("[WARN] bcrypt not installed, falling back to SHA256")

# python-jose
try:
    from jose import jwt, JWTError
    HAS_JOSE = True
except ImportError:
    HAS_JOSE = False

# ========== 配置 ==========
DB_PATH = Path(__file__).parent / "users.db"
WEB_DIR = Path(__file__).parent / "web"
SECRET_KEY = os.environ.get("IDI_SECRET_KEY", "idi-defects-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

# 登录锁定配置
MAX_LOGIN_ATTEMPTS = 5          # 最大失败次数
LOCKOUT_DURATION_MINUTES = 15   # 锁定时长（分钟）

# 密码复杂度
PASSWORD_MIN_LENGTH = 8
PASSWORD_PATTERN = re.compile(r'^(?=.*[a-zA-Z])(?=.*\d).+$')  # 至少一个字母+一个数字

# ========== 数据库 ==========
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # WAL 模式提升并发性能
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA synchronous=NORMAL")

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)
    # 迁移：添加 is_admin 字段
    try:
        c.execute("SELECT is_admin FROM users LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")

    # 统计表
    c.execute("""
        CREATE TABLE IF NOT EXISTS stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            user TEXT,
            ip TEXT,
            created_at TEXT NOT NULL
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_stats_date ON stats(date)")

    # 登录失败记录表（用于锁定）
    c.execute("""
        CREATE TABLE IF NOT EXISTS login_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            ip TEXT,
            success INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_login_attempts_user ON login_attempts(username, created_at)")

    conn.commit()
    conn.close()


# ========== 密码工具（bcrypt + 兼容旧 SHA256） ==========
def hash_password(password: str) -> str:
    """使用 bcrypt 哈希密码"""
    if HAS_BCRYPT:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()
    # fallback
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """验证密码，支持 bcrypt 和旧版 SHA256"""
    if not password_hash:
        return False

    # 尝试 bcrypt（bcrypt hash 以 $2b$ 开头）
    if HAS_BCRYPT and password_hash.startswith(("$2a$", "$2b$", "$2y$", "$2x$")):
        return bcrypt.checkpw(password.encode(), password_hash.encode())

    # 兼容旧版 SHA256（64位十六进制）
    if len(password_hash) == 64:
        return hmac.compare_digest(hashlib.sha256(password.encode()).hexdigest(), password_hash)

    return False


def password_complexity(password: str) -> tuple[bool, str]:
    """检查密码复杂度，返回 (是否通过, 错误信息)"""
    if len(password) < PASSWORD_MIN_LENGTH:
        return False, f"密码至少{PASSWORD_MIN_LENGTH}位"
    if not PASSWORD_PATTERN.match(password):
        return False, "密码必须同时包含字母和数字"
    return True, ""


# ========== 登录锁定 ==========
def record_login_attempt(username: str, ip: str = None, success: bool = False):
    """记录一次登录尝试"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "INSERT INTO login_attempts (username, ip, success, created_at) VALUES (?, ?, ?, ?)",
            (username, ip or "", 1 if success else 0, datetime.now().isoformat())
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def is_account_locked(username: str) -> tuple[bool, str]:
    """检查账户是否被锁定，返回 (是否锁定, 提示信息)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        since = (datetime.now() - timedelta(minutes=LOCKOUT_DURATION_MINUTES)).isoformat()

        # 最近 LOCKOUT_DURATION_MINUTES 内的失败次数
        c.execute(
            "SELECT COUNT(*) FROM login_attempts WHERE username = ? AND success = 0 AND created_at > ?",
            (username, since)
        )
        failed = c.fetchone()[0]

        # 最近一次成功登录时间
        c.execute(
            "SELECT MAX(created_at) FROM login_attempts WHERE username = ? AND success = 1",
            (username,)
        )
        last_success = c.fetchone()[0]

        conn.close()

        if failed >= MAX_LOGIN_ATTEMPTS:
            if last_success and last_success > since:
                # 最近有成功登录，重置计数
                return False, ""
            return True, f"登录失败次数过多，账户已锁定{LOCKOUT_DURATION_MINUTES}分钟"

        return False, ""
    except Exception:
        return False, ""


def clear_login_attempts(username: str):
    """清除用户的登录失败记录（成功登录后调用）"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM login_attempts WHERE username = ? AND success = 0", (username,))
        conn.commit()
        conn.close()
    except Exception:
        pass


# ========== JWT 工具 ==========
def _fallback_sign(username: str) -> str:
    return hashlib.sha256(f"{username}{SECRET_KEY}".encode()).hexdigest()[:16]


def create_access_token(data: dict, expires_delta: timedelta = None):
    if not HAS_JOSE:
        username = data['sub']
        payload = base64.b64encode(username.encode()).decode().rstrip('=')
        sig = _fallback_sign(username)
        return f"{payload}.{sig}"
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> str:
    if not HAS_JOSE:
        try:
            parts = token.split('.')
            if len(parts) != 2:
                return None
            payload_b64 = parts[0]
            padding = 4 - len(payload_b64) % 4
            if padding != 4:
                payload_b64 += '=' * padding
            username = base64.b64decode(payload_b64).decode()
            expected_sig = _fallback_sign(username)
            if hmac.compare_digest(parts[1], expected_sig):
                return username
        except Exception:
            pass
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


# ========== 访问统计 ==========
def record_visit(username: str = None, ip: str = None):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        c.execute(
            "INSERT INTO stats (date, user, ip, created_at) VALUES (?, ?, ?, ?)",
            (today, username or "anonymous", ip or "", datetime.now().isoformat())
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def get_stats():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        c.execute("SELECT COUNT(*) FROM stats WHERE date = ?", (today,))
        today_visits = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM stats")
        total_visits = c.fetchone()[0]
        c.execute("SELECT COUNT(DISTINCT user) FROM stats WHERE date = ?", (today,))
        today_users = c.fetchone()[0]
        c.execute("SELECT COUNT(DISTINCT user) FROM stats")
        total_users = c.fetchone()[0]
        c.execute("""
            SELECT date, COUNT(*) FROM stats
            WHERE date >= date('now', '-6 days')
            GROUP BY date ORDER BY date
        """)
        daily = [{"date": r[0], "count": r[1]} for r in c.fetchall()]
        conn.close()
        return {
            "today_visits": today_visits,
            "total_visits": total_visits,
            "today_users": today_users,
            "total_users": total_users,
            "daily": daily,
        }
    except Exception:
        return {
            "today_visits": 0, "total_visits": 0,
            "today_users": 0, "total_users": 0, "daily": []
        }


def get_stats_detail(limit: int = 200):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            SELECT user, ip, created_at FROM stats
            ORDER BY created_at DESC LIMIT ?
        """, (limit,))
        records = [{"user": r[0], "ip": r[1], "time": r[2]} for r in c.fetchall()]
        c.execute("""
            SELECT user, COUNT(*) as cnt, MAX(created_at) as last_time
            FROM stats GROUP BY user ORDER BY cnt DESC
        """)
        by_user = [{"user": r[0], "count": r[1], "last_time": r[2]} for r in c.fetchall()]
        conn.close()
        return {"records": records, "by_user": by_user}
    except Exception:
        return {"records": [], "by_user": []}


# ========== Pydantic 模型 ==========
REGISTER_CODE = os.environ.get("IDI_REGISTER_CODE", "zchidi")


class UserRegister(BaseModel):
    username: str
    password: str
    remember: bool = False
    code: str = ""


class UserLogin(BaseModel):
    username: str
    password: str
    remember: bool = False


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class CreateUserBody(BaseModel):
    username: str
    password: str
    is_admin: bool = False


class ResetPasswordBody(BaseModel):
    new_password: str


class DefectBody(BaseModel):
    category_period: str
    category_major: str
    category_minor: str
    problem: str
    suggestion: str
    image: str = ""


# ========== FastAPI 应用 ==========
app = FastAPI(title="IDI 缺陷速查认证服务")
security = HTTPBearer(auto_error=False)


@app.on_event("startup")
def startup():
    init_db()


# ========== 依赖 ==========
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


# ========== 认证路由 ==========
@app.post("/api/auth/register", response_model=TokenResponse)
def register(body: UserRegister):
    if len(body.username) < 3 or len(body.username) > 20:
        raise HTTPException(status_code=400, detail="用户名长度3-20位")

    ok, msg = password_complexity(body.password)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    if body.code != REGISTER_CODE:
        raise HTTPException(status_code=400, detail="注册密令错误")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO users (username, password_hash, is_admin, created_at) VALUES (?, ?, ?, ?)",
            (body.username, hash_password(body.password), 0, datetime.now().isoformat())
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
def login(body: UserLogin, request: Request):
    """用户登录（带失败锁定）"""
    client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "")

    # 检查账户是否被锁定
    locked, lock_msg = is_account_locked(body.username)
    if locked:
        raise HTTPException(status_code=429, detail=lock_msg)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT password_hash FROM users WHERE username = ?", (body.username,))
    row = c.fetchone()
    conn.close()

    if not row or not verify_password(body.password, row[0]):
        record_login_attempt(body.username, client_ip, success=False)
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 登录成功：清除失败记录 + 记录成功
    clear_login_attempts(body.username)
    record_login_attempt(body.username, client_ip, success=True)

    expire_days = 365 if body.remember else 7
    token = create_access_token({"sub": body.username}, expires_delta=timedelta(days=expire_days))
    return {"access_token": token, "token_type": "bearer"}


@app.get("/api/auth/me")
def me(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="未登录")
    username = decode_token(credentials.credentials)
    if not username:
        raise HTTPException(status_code=401, detail="登录已过期")
    return {"username": username}


# ========== 健康检查 ==========
@app.get("/_health")
def health_check():
    return {"status": "ok", "time": datetime.now().isoformat()}


# ========== 静态资源 ==========
@app.get("/defects.json")
def get_defects(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="未登录")
    username = decode_token(credentials.credentials)
    if not username:
        raise HTTPException(status_code=401, detail="登录已过期")

    record_visit(username=username)
    defects_path = WEB_DIR / "defects.json"
    if not defects_path.exists():
        raise HTTPException(status_code=404, detail="数据文件不存在")
    return FileResponse(defects_path)


@app.get("/", response_class=HTMLResponse)
def index():
    index_path = WEB_DIR / "index.html"
    if index_path.exists():
        return index_path.read_text(encoding="utf-8")
    raise HTTPException(status_code=404)


@app.get("/imgs/{filename}")
def img_file(filename: str):
    file_path = WEB_DIR / "imgs" / filename
    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)
    raise HTTPException(status_code=404)


@app.get("/{filename}")
def static_file(filename: str):
    file_path = WEB_DIR / filename
    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)
    raise HTTPException(status_code=404)


# ========== 管理员 API ==========
@app.get("/api/admin/check")
def admin_check(username: str = Depends(get_current_username)):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT is_admin FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    return {"is_admin": bool(row and row[0]), "username": username}


@app.get("/api/stats")
def stats_endpoint(admin: str = Depends(require_admin)):
    return get_stats()


@app.get("/api/stats/detail")
def stats_detail_endpoint(admin: str = Depends(require_admin)):
    return get_stats_detail()


@app.get("/api/admin/users")
def admin_list_users(admin: str = Depends(require_admin)):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, username, is_admin, created_at FROM users ORDER BY id")
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "username": r[1], "is_admin": bool(r[2]), "created_at": r[3]} for r in rows]


@app.post("/api/admin/users")
def admin_create_user(body: CreateUserBody, admin: str = Depends(require_admin)):
    if len(body.username) < 3 or len(body.username) > 20:
        raise HTTPException(status_code=400, detail="用户名长度3-20位")
    ok, msg = password_complexity(body.password)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

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


@app.post("/api/admin/users/{username}/reset")
def admin_reset_password(username: str, body: ResetPasswordBody, admin: str = Depends(require_admin)):
    ok, msg = password_complexity(body.new_password)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
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


# ========== 缺陷管理 API ==========
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

    img_path = WEB_DIR / "imgs" / f"{global_id}.jpg"
    if img_path.exists():
        img_path.unlink()

    with open(defects_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return {"ok": True}


# ========== 图片上传 API ==========
from fastapi import UploadFile, File as FastAPIFile


@app.post("/api/admin/upload")
async def admin_upload_image(
    file: UploadFile = FastAPIFile(...),
    admin: str = Depends(require_admin)
):
    import shutil
    from PIL import Image

    temp_path = WEB_DIR / "imgs" / file.filename
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

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
