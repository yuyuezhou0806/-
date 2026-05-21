@echo off
chcp 65001 >nul
echo ========================================
echo      车辆档案管理系统 - 一键安装
echo ========================================
echo.

:: 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    echo.
    pause
    exit
)

echo [1/3] 检测到Python:
python --version
echo.

:: 安装依赖
echo [2/3] 正在安装依赖包...
pip install -r requirements.txt
if errorlevel 1 (
    echo [错误] 依赖安装失败，请检查网络连接
    pause
    exit
)
echo [完成] 依赖安装完成
echo.

:: 启动服务
echo [3/3] 正在启动系统...
echo 启动完成后会自动打开浏览器...
echo.

start http://localhost:8000/index.html
python main.py

pause
