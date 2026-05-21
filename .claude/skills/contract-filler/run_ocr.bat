@echo off
chcp 65001 >nul
echo ========================================
echo      合同自动填充工具 (OCR版)
echo ========================================
echo.
echo 用法:
echo   1. 把网页截图保存为图片（如 screenshot.png）
echo   2. 把图片拖到这个 bat 文件上
echo   3. 或双击运行后输入图片路径
echo.

set "SCRIPT_DIR=%~dp0"
set "PY_SCRIPT=%SCRIPT_DIR%contract_filler_ocr.py"

if "%~1"=="" (
    set /p "IMAGE=截图图片路径: "
    if "!IMAGE!"=="" exit /b
) else (
    set "IMAGE=%~1"
)

if not exist "%IMAGE%" (
    echo [X] 图片不存在: %IMAGE%
    pause
    exit /b 1
)

echo.
echo [*] 正在识别图片并填充合同...
python "%PY_SCRIPT%" "%IMAGE%"

echo.
pause
