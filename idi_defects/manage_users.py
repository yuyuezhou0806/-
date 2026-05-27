"""
IDI 缺陷速查 - 用户管理工具
查看、删除注册用户
"""

import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent / "users.db"

def list_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, username, created_at FROM users ORDER BY id")
    rows = c.fetchall()
    conn.close()

    if not rows:
        print("还没有注册用户")
        return

    print(f"\n{'ID':<4} {'用户名':<20} {'注册时间'}")
    print("-" * 50)
    for row in rows:
        print(f"{row[0]:<4} {row[1]:<20} {row[2]}")
    print(f"\n共 {len(rows)} 个用户\n")

def delete_user(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE username = ?", (username,))
    if c.rowcount == 0:
        print(f"用户 '{username}' 不存在")
    else:
        print(f"用户 '{username}' 已删除")
    conn.commit()
    conn.close()

def reset_password(username, new_password):
    import hashlib
    password_hash = hashlib.sha256(new_password.encode()).hexdigest()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET password_hash = ? WHERE username = ?", (password_hash, username))
    if c.rowcount == 0:
        print(f"用户 '{username}' 不存在")
    else:
        print(f"用户 '{username}' 密码已重置为: {new_password}")
    conn.commit()
    conn.close()

def show_help():
    print("""
IDI 用户管理工具

用法:
  python manage_users.py list              查看所有用户
  python manage_users.py delete 用户名     删除指定用户
  python manage_users.py reset 用户名 新密码  重置密码

示例:
  python manage_users.py list
  python manage_users.py delete testuser
  python manage_users.py reset testuser 123456
""")

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        show_help()
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "list":
        list_users()
    elif cmd == "delete":
        if len(sys.argv) < 3:
            print("错误: 请指定要删除的用户名")
            print("用法: python manage_users.py delete 用户名")
        else:
            delete_user(sys.argv[2])
    elif cmd == "reset":
        if len(sys.argv) < 4:
            print("错误: 请指定用户名和新密码")
            print("用法: python manage_users.py reset 用户名 新密码")
        else:
            reset_password(sys.argv[2], sys.argv[3])
    else:
        print(f"未知命令: {cmd}")
        show_help()
