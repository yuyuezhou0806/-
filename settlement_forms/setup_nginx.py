#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import paramiko

SERVER_IP = "1.15.170.85"
USER = "ubuntu"
PASSWORD = "JMXU:6WfdgH3n-Q="

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(SERVER_IP, username=USER, password=PASSWORD, timeout=15)

def run(cmd, sudo=False):
    if sudo:
        cmd = f"echo '{PASSWORD}' | sudo -S bash -c '{cmd}'"
    stdin, stdout, stderr = client.exec_command(cmd)
    return stdout.read().decode('utf-8', errors='ignore'), stderr.read().decode('utf-8', errors='ignore')

# 1. Fix frontend JS path in web_app.py
print("[1/3] 修改前端路径为相对路径...")
run("sed -i \"s|fetch('/generate'|fetch('./generate'|g\" /home/ubuntu/settlement-form/web_app.py")

# 2. Add nginx location
print("[2/3] 配置 nginx 反代...")
nginx_block = """
    # settlement-form
    location /settlement/ {
        proxy_pass http://127.0.0.1:8080/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}"""

# Read current config
out, err = run("cat /etc/nginx/sites-enabled/idi-defects")
# Remove trailing } if present and append new block
config = out.rstrip()
if config.endswith('}'):
    config = config[:-1]
config += nginx_block

# Write back
run(f"cat > /tmp/nginx_new.conf << 'EOF'\n{config}\nEOF", sudo=True)
run("cp /tmp/nginx_new.conf /etc/nginx/sites-enabled/idi-defects", sudo=True)

# Test nginx
print("  测试 nginx 配置...")
out, err = run("nginx -t", sudo=True)
if "successful" in out or "successful" in err:
    print("  nginx 配置测试通过")
else:
    print(f"  nginx 测试: {out} {err}")

# Reload nginx
print("  重载 nginx...")
run("systemctl reload nginx", sudo=True)

# 3. Restart service
print("[3/3] 重启结算报审单服务...")
run("systemctl restart settlement-form", sudo=True)

# Check status
out, err = run("systemctl is-active settlement-form", sudo=True)
print(f"  服务状态: {out.strip()}")

print()
print("完成！访问地址: http://1.15.170.85/settlement/")

client.close()
