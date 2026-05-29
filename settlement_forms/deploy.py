#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自动部署脚本 - 用 paramiko 把结算报审单网页版部署到 Ubuntu 服务器

用法:
    python deploy.py
"""

import os
import sys
import time
import io

import paramiko

# ========== 配置 ==========
SERVER_IP = "1.15.170.85"
USER = "ubuntu"
PASSWORD = "JMXU:6WfdgH3n-Q="
REMOTE_DIR = "/home/ubuntu/settlement-form"
PORT = 8080
# ==========================

LOCAL_DIR = os.path.dirname(os.path.abspath(__file__))
FILES_TO_UPLOAD = ["web_app.py", "template.docx"]


def get_ssh_client():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(SERVER_IP, username=USER, password=PASSWORD, timeout=15)
    return client


def run_cmd(client, cmd, sudo=False):
    """在远程执行命令"""
    if sudo:
        cmd = f"echo '{PASSWORD}' | sudo -S {cmd}"
    stdin, stdout, stderr = client.exec_command(cmd)
    exit_code = stdout.channel.recv_exit_status()
    out = stdout.read().decode("utf-8", errors="ignore")
    err = stderr.read().decode("utf-8", errors="ignore")
    return exit_code, out, err


def upload_file(sftp, local_path, remote_path):
    """上传单个文件"""
    print(f"    上传: {os.path.basename(local_path)}")
    sftp.put(local_path, remote_path)


def main():
    print(f"部署目标: {USER}@{SERVER_IP}:{PORT}")
    print(f"本地目录: {LOCAL_DIR}")
    print()

    client = None
    sftp = None

    try:
        # 1. 连接服务器
        print("[1/6] 连接服务器...")
        client = get_ssh_client()
        print("  连接成功")

        # 2. 创建远程目录
        print("[2/6] 创建远程目录...")
        run_cmd(client, f"mkdir -p {REMOTE_DIR}")
        print("  完成")

        # 3. 上传文件
        print("[3/6] 上传文件...")
        sftp = client.open_sftp()
        for fname in FILES_TO_UPLOAD:
            local = os.path.join(LOCAL_DIR, fname)
            if not os.path.exists(local):
                print(f"  错误: 本地文件不存在 {local}")
                sys.exit(1)
            upload_file(sftp, local, f"{REMOTE_DIR}/{fname}")
        sftp.close()
        print("  全部上传完成")

        # 4. 安装依赖
        print("[4/6] 安装 Python 依赖...")
        deps = "python-docx pandas openpyxl fastapi uvicorn python-multipart"
        code, out, err = run_cmd(client, f"cd {REMOTE_DIR} && pip3 install {deps} --user -q 2>&1")
        if code != 0:
            print(f"  警告: 安装输出: {err or out}")
        else:
            print("  依赖安装完成")

        # 5. 创建并启动 systemd 服务
        print("[5/6] 配置 systemd 服务...")
        service_content = f"""[Unit]
Description=Settlement Form Generator
After=network.target

[Service]
Type=simple
User={USER}
WorkingDirectory={REMOTE_DIR}
ExecStart=/usr/bin/python3 {REMOTE_DIR}/web_app.py
Restart=always
RestartSec=5
Environment=PORT={PORT}

[Install]
WantedBy=multi-user.target
"""
        # 用 echo 写入服务文件
        service_escaped = service_content.replace("'", "'\"'\"'").replace("\n", "\\n")
        write_cmd = f"echo -e '{service_escaped}' | sudo tee /etc/systemd/system/settlement-form.service > /dev/null"
        code, out, err = run_cmd(client, write_cmd, sudo=True)

        run_cmd(client, "systemctl daemon-reload", sudo=True)
        run_cmd(client, "systemctl enable settlement-form", sudo=True)
        print("  服务配置完成")

        # 6. 启动服务
        print("[6/6] 启动服务...")
        run_cmd(client, "systemctl restart settlement-form", sudo=True)
        time.sleep(2)

        code, out, err = run_cmd(client, "systemctl is-active settlement-form", sudo=True)
        if out.strip() == "active":
            print("  服务启动成功!")
        else:
            print(f"  服务状态: {out.strip()}")
            _, log_out, _ = run_cmd(client, "journalctl -u settlement-form -n 20 --no-pager", sudo=True)
            print(f"  最近日志:\n{log_out}")

        print()
        print("=" * 50)
        print(f"部署完成!")
        print(f"访问地址: http://{SERVER_IP}:{PORT}")
        print("=" * 50)
        print()
        print("常用命令:")
        print(f"  查看状态: ssh {USER}@{SERVER_IP} 'sudo systemctl status settlement-form'")
        print(f"  查看日志: ssh {USER}@{SERVER_IP} 'sudo journalctl -u settlement-form -f'")
        print(f"  重启服务: ssh {USER}@{SERVER_IP} 'sudo systemctl restart settlement-form'")
        print(f"  停止服务: ssh {USER}@{SERVER_IP} 'sudo systemctl stop settlement-form'")

    except paramiko.AuthenticationException:
        print("错误: 认证失败，请检查用户名和密码")
        sys.exit(1)
    except paramiko.SSHException as e:
        print(f"错误: SSH 连接失败 - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)
    finally:
        if sftp:
            try:
                sftp.close()
            except:
                pass
        if client:
            client.close()


if __name__ == "__main__":
    main()
