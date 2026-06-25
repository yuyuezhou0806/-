"""
IDI 缺陷速查 - 数据库备份脚本
每周自动从腾讯云服务器下载 users.db 到本地备份
"""
import paramiko
import os
import shutil
from datetime import datetime
from pathlib import Path

# ========== 配置 ==========
SERVER_HOST = "1.15.170.85"
SERVER_USER = "ubuntu"
SERVER_PASS = os.environ.get("IDI_SSH_PASSWORD", "")
REMOTE_DB_PATH = "/var/www/idi-defects/users.db"

# 本地备份目录（脚本所在目录下的 backups 文件夹）
BACKUP_DIR = Path(__file__).parent / "backups"
KEEP_BACKUPS = 10  # 保留最近10份备份


def export_txt(db_path: Path):
    """把 SQLite 数据库导出为 TXT（用户表 + 统计表）"""
    try:
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        txt_path = str(db_path).replace(".db", ".txt")

        lines = []
        lines.append("=" * 60)
        lines.append(f"IDI 用户数据库备份 - {db_path.name}")
        lines.append(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 60)

        # users 表
        lines.append("\n【用户表 (users)】")
        lines.append("-" * 60)
        c.execute("SELECT id, username, is_admin, created_at FROM users ORDER BY id")
        rows = c.fetchall()
        lines.append(f"总数: {len(rows)} 人")
        lines.append("")
        lines.append(f"{'ID':<4} {'用户名':<20} {'权限':<8} {'创建时间'}")
        lines.append("-" * 60)
        for r in rows:
            role = "管理员" if r[2] else "普通用户"
            lines.append(f"{r[0]:<4} {r[1]:<20} {role:<8} {r[3]}")

        # stats 表
        lines.append("\n")
        lines.append("=" * 60)
        lines.append("【访问统计 (stats)】")
        lines.append("-" * 60)
        c.execute("SELECT COUNT(*) FROM stats")
        total = c.fetchone()[0]
        lines.append(f"总访问记录: {total} 条")

        if total > 0:
            c.execute("SELECT user, COUNT(*) as cnt FROM stats GROUP BY user ORDER BY cnt DESC")
            lines.append("\n按用户统计:")
            lines.append(f"{'用户名':<20} {'次数'}")
            lines.append("-" * 30)
            for r in c.fetchall():
                lines.append(f"{r[0]:<20} {r[1]}")

            c.execute("SELECT date, user, ip, created_at FROM stats ORDER BY created_at DESC LIMIT 50")
            lines.append("\n最近 50 条访问记录:")
            lines.append(f"{'时间':<25} {'用户':<15} {'IP'}")
            lines.append("-" * 60)
            for r in c.fetchall():
                lines.append(f"{r[3]:<25} {r[1]:<15} {r[2] or '-'}")

        conn.close()

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"  已导出 TXT: {Path(txt_path).name}")

    except Exception as e:
        print(f"  TXT 导出失败: {e}")


def backup():
    if not SERVER_PASS:
        raise RuntimeError("请先设置环境变量 IDI_SSH_PASSWORD")

    BACKUP_DIR.mkdir(exist_ok=True)

    # 生成本地备份文件名（带时间戳）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    local_backup = BACKUP_DIR / f"users_db_{timestamp}.db"

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始备份...")
    print(f"  服务器: {SERVER_HOST}")
    print(f"  远程文件: {REMOTE_DB_PATH}")
    print(f"  本地保存: {local_backup}")

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(SERVER_HOST, username=SERVER_USER, password=SERVER_PASS, timeout=30)

        sftp = client.open_sftp()
        sftp.get(REMOTE_DB_PATH, str(local_backup))
        sftp.close()
        client.close()

        # 同时更新当前使用的 users.db（覆盖本地最新版）
        current_db = Path(__file__).parent / "users.db"
        shutil.copy2(str(local_backup), str(current_db))
        print(f"  已同步到本地 users.db")

        # 导出为 TXT（方便直接查看）
        export_txt(local_backup)

        print(f"  备份成功: {local_backup.name}")

        # 清理旧备份，只保留最近 KEEP_BACKUPS 份
        backups = sorted(BACKUP_DIR.glob("users_db_*.db"), key=lambda p: p.stat().st_mtime)
        if len(backups) > KEEP_BACKUPS:
            for old in backups[:-KEEP_BACKUPS]:
                old.unlink()
                txt_old = old.with_suffix(".txt")
                if txt_old.exists():
                    txt_old.unlink()
                print(f"  清理旧备份: {old.name}")

        print("  完成")
        return True

    except Exception as e:
        print(f"  备份失败: {e}")
        return False


if __name__ == "__main__":
    success = backup()
    input("\n按 Enter 键退出...") if os.environ.get("INTERACTIVE") else None
