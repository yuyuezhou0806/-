"""检测行业 Agent 部署脚本"""
import paramiko
import os

HOST = "1.15.170.85"
USER = "ubuntu"
PASS = "JMXU:6WfdgH3n-Q="
REMOTE = "/var/www/inspection-agent"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=15)

# 上传代码
sftp = client.open_sftp()
local_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
files = [
    "backend/main.py",
    "backend/database.py",
    "backend/agent.py",
]
for f in files:
    local = os.path.join(local_base, f)
    remote = f"{REMOTE}/{f}"
    print(f"Upload {f}")
    sftp.put(local, remote)

# 上传 systemd 服务
service_local = os.path.join(local_base, "deploy", "inspection-agent.service")
sftp.put(service_local, "/tmp/inspection-agent.service")
sftp.close()

# 安装服务
print("Installing systemd service...")
cmds = [
    f"sudo cp /tmp/inspection-agent.service /etc/systemd/system/",
    "sudo systemctl daemon-reload",
    "sudo systemctl enable inspection-agent",
    "sudo systemctl restart inspection-agent",
    "sleep 2",
    "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/health",
]
for cmd in cmds:
    stdin, stdout, stderr = client.exec_command(cmd, timeout=15)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out: print(f"  {cmd[:50]}... -> {out}")
    if err and "Warning" not in err: print(f"  ERR: {err}")

client.close()
print("[DONE]")
