@echo off
chcp 65001 >nul
echo ========================================
echo   安装 PDF-CAD 工具依赖
echo ========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [X] 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

echo [*] 正在安装 ezdxf, pikepdf, matplotlib ...
pip install ezdxf pikepdf matplotlib -q

if errorlevel 1 (
    echo [X] 安装失败
) else (
    echo [OK] 安装完成
)

echo.
pause
