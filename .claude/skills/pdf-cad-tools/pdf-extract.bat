@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "PY_SCRIPT=%SCRIPT_DIR%pdf_tools.py"

if "%~1"=="" (
    echo ========================================
    echo   PDF 页面提取工具
echo ========================================
    echo.
    echo 用法:
    echo   把 .pdf 文件拖到这个图标上
echo.
    echo 页码格式: 1,3,5   或   5-10   或   1,3,5-10
echo.
    set /p "INPUT=请输入 PDF 文件路径: "
    if "!INPUT!"=="" exit /b
) else (
    set "INPUT=%~1"
)

set /p "PAGES=要提取的页码: "
if "!PAGES!"=="" (
    echo [X] 页码不能为空
    pause
    exit /b
)

set /p "OUTPUT=输出文件名（默认 extracted.pdf）: "
if "!OUTPUT!"=="" set "OUTPUT=extracted.pdf"

echo.
echo [*] 正在提取页面...
python "%PY_SCRIPT%" extract "%INPUT%" "%PAGES%" -o "%OUTPUT%"

echo.
pause
