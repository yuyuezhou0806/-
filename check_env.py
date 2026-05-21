#!/usr/bin/env python3
"""
环境检查脚本 - 运行后告诉我结果
"""

import subprocess
import sys

def check_command(cmd, name):
    """检查命令是否可用"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {name}: 已安装")
            return True
        else:
            print(f"❌ {name}: 未安装")
            return False
    except:
        print(f"❌ {name}: 未安装")
        return False

def check_python_package(package):
    """检查Python包是否安装"""
    try:
        __import__(package)
        print(f"✅ {package}: 已安装")
        return True
    except ImportError:
        print(f"❌ {package}: 未安装 (需要: pip install {package})")
        return False

print("=" * 50)
print("环境检查报告")
print("=" * 50)

print("\n【Python 环境】")
print(f"Python版本: {sys.version}")

print("\n【必要Python包】")
packages = ['fastapi', 'uvicorn', 'sqlalchemy', 'pydantic']
for pkg in packages:
    check_python_package(pkg)

print("\n【可选工具】")
check_command("git --version", "Git")

print("\n" + "=" * 50)
print("检查完成！把上面结果截图给我")
print("=" * 50)
