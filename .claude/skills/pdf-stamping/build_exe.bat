@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================
echo PDF 盖章工具 - PyInstaller 打包脚本
echo ============================================

REM 检查 pyinstaller
where pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [!] 未安装 pyinstaller, 正在安装...
    pip install pyinstaller
    if errorlevel 1 (
        echo [X] pyinstaller 安装失败
        pause
        exit /b 1
    )
)

echo [*] 开始打包...
pyinstaller --noconfirm --clean ^
    --onefile ^
    --windowed ^
    --name "PDF盖章工具" ^
    --hidden-import "PIL._tkinter_finder" ^
    pdf_stamping.py

if errorlevel 1 (
    echo [X] 打包失败
    pause
    exit /b 1
)

echo.
echo [OK] 打包完成!
echo 输出: dist\PDF盖章工具.exe
echo.

REM 清理中间文件
rmdir /s /q build 2>nul
del /q "PDF盖章工具.spec" 2>nul

pause
