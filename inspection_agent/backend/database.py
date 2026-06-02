"""SQLite 数据库 — 对话记忆 + 用量统计"""
import sqlite3, json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "agent.db"

def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY, title TEXT, messages TEXT,
            created_at TEXT, updated_at TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS usage_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, query TEXT,
            tools_used TEXT, response_len INTEGER, user_agent TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_conversation(conv_id: str, title: str, messages: list):
    conn = get_db()
    now = datetime.now().isoformat()
    conn.execute("""
        INSERT OR REPLACE INTO conversations (id, title, messages, created_at, updated_at)
        VALUES (?, ?, ?, COALESCE((SELECT created_at FROM conversations WHERE id=?), ?), ?)
    """, [conv_id, title, json.dumps(messages, ensure_ascii=False), conv_id, now, now])
    conn.commit(); conn.close()

def list_conversations(limit=50):
    conn = get_db()
    rows = conn.execute("SELECT id,title,created_at,updated_at FROM conversations ORDER BY updated_at DESC LIMIT ?", [limit]).fetchall()
    conn.close()
    return [{"id": r["id"], "title": r["title"], "created_at": r["created_at"], "updated_at": r["updated_at"]} for r in rows]

def delete_conversation(conv_id: str):
    conn = get_db()
    conn.execute("DELETE FROM conversations WHERE id=?", [conv_id])
    conn.commit(); conn.close()

def log_usage(query: str, tools_used: list, response_len: int, user_agent: str = ""):
    conn = get_db()
    conn.execute("INSERT INTO usage_logs (query, tools_used, response_len, user_agent, created_at) VALUES (?,?,?,?,?)",
        [query, json.dumps(tools_used), response_len, user_agent, datetime.now().isoformat()])
    conn.commit(); conn.close()

def get_usage_stats():
    conn = get_db()
    today = datetime.now().strftime("%Y-%m-%d")
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM usage_logs WHERE date(created_at)=?", [today])
    today_q = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM usage_logs")
    total_q = c.fetchone()[0]
    c.execute("SELECT AVG(response_len) FROM usage_logs")
    avg_len = int(c.fetchone()[0] or 0)
    c.execute("SELECT tools_used FROM usage_logs ORDER BY id DESC LIMIT 200")
    tool_counts = {}
    for row in c.fetchall():
        for t in json.loads(row["tools_used"] or "[]"):
            tool_counts[t] = tool_counts.get(t, 0) + 1
    c.execute("SELECT date(created_at) as d, COUNT(*) as c FROM usage_logs WHERE created_at >= date('now','-30 days') GROUP BY d ORDER BY d")
    daily = [{"date": r["d"], "count": r["c"]} for r in c.fetchall()]
    conn.close()
    return {"today_queries": today_q, "total_queries": total_q, "avg_response_len": avg_len, "tool_usage": tool_counts, "daily": daily}

init_db()
