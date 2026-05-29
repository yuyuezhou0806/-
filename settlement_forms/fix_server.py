#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一键修复 nginx 配置"""

import paramiko

SERVER_IP = "1.15.170.85"
USER = "ubuntu"
PASSWORD = "JMXU:6WfdgH3n-Q="

print("正在连接服务器...")
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(SERVER_IP, username=USER, password=PASSWORD, timeout=15)

nginx_config = r'''server {
    listen 80;
    server_name _;

    # idi-defects
    location / {
        root /var/www/idi-defects/web;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    location /imgs/ {
        alias /var/www/idi-defects/web/imgs/;
        expires 7d;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:5173;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
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
        try_files $uri $uri/ /agent/index.html;
    }

    # inspection-agent backend API
    location /inspection/ {
        proxy_pass http://127.0.0.1:8001/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_buffering off;
    }

    # settlement-form
    location /settlement/ {
        proxy_pass http://127.0.0.1:8080/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
'''

print("写入 nginx 配置...")
sftp = client.open_sftp()
with sftp.file('/tmp/nginx_fix.conf', 'w') as f:
    f.write(nginx_config)
sftp.close()

print("替换配置...")
stdin, stdout, stderr = client.exec_command("echo '%s' | sudo -S cp /tmp/nginx_fix.conf /etc/nginx/sites-enabled/idi-defects" % PASSWORD)

print("测试配置...")
stdin, stdout, stderr = client.exec_command("echo '%s' | sudo -S nginx -t" % PASSWORD)
out = stdout.read().decode('utf-8', errors='ignore').strip()
err = stderr.read().decode('utf-8', errors='ignore').strip()
result = out or err
print("  ", result)

if "successful" in result:
    print("重载 nginx...")
    stdin, stdout, stderr = client.exec_command("echo '%s' | sudo -S systemctl reload nginx" % PASSWORD)
    print("  完成!")
    print()
    print("修复完成，请刷新以下页面：")
    print("  http://1.15.170.85/")
    print("  http://1.15.170.85/agent/")
    print("  http://1.15.170.85/settlement/")
else:
    print("配置测试失败，请检查错误信息")

client.close()
input("\n按回车键退出...")
