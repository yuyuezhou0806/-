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
        cmd = f"echo '{PASSWORD}' | sudo -S bash -c \"{cmd}\""
    stdin, stdout, stderr = client.exec_command(cmd)
    return stdout.read().decode('utf-8', errors='ignore'), stderr.read().decode('utf-8', errors='ignore')

# Write complete correct nginx config
nginx_config = r'''server {
    listen 80;
    server_name _;

    # idi-defects
    location / {
        root /var/www/idi-defects/web;
        index index.html;
        try_files \$uri \$uri/ =404;
    }

    location /imgs/ {
        alias /var/www/idi-defects/web/imgs/;
        expires 7d;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:5173;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }

    # inspection-agent _next static assets
    location /_next/ {
        alias /var/www/inspection-agent/dist/_next/;
        expires 30d;
    }

    # inspection-agent frontend
    location /agent/ {
        alias /var/www/inspection-agent/dist/;
        index index.html;
        try_files \$uri \$uri/ /agent/index.html;
    }

    # inspection-agent backend API
    location /inspection/ {
        proxy_pass http://127.0.0.1:8001/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_buffering off;
    }

    # settlement-form
    location /settlement/ {
        proxy_pass http://127.0.0.1:8080/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
'''

print("[1/3] 修复 nginx 配置...")
# Write to temp file then sudo copy
sftp = client.open_sftp()
with sftp.file('/tmp/nginx_settlement.conf', 'w') as f:
    f.write(nginx_config)
sftp.close()

run('cp /tmp/nginx_settlement.conf /etc/nginx/sites-enabled/idi-defects', sudo=True)

print("[2/3] 测试 nginx 配置...")
out, err = run('nginx -t', sudo=True)
print(f"  stdout: {out}")
print(f"  stderr: {err}")

print("[3/3] 重载 nginx...")
run('systemctl reload nginx', sudo=True)

# Also fix web_app.py JS path
print("修复前端 JS 路径...")
run("sed -i \"s|fetch('/generate'|fetch('./generate'|g\" /home/ubuntu/settlement-form/web_app.py")

# Restart service
run('systemctl restart settlement-form', sudo=True)
out, err = run('systemctl is-active settlement-form', sudo=True)
print(f"服务状态: {out.strip()}")

print()
print("完成！访问地址: http://1.15.170.85/settlement/")

client.close()
