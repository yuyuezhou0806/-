@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "PY_SCRIPT=%SCRIPT_DIR%pdf_tools.py"

if "%~1"=="" (
    echo ========================================
    echo   PDF 拆分工具
echo ========================================
    echo.
    echo 用法:
    echo   把 .pdf 文件拖到这个图标上
echo.
    set /p "INPUT=请输入 PDF 文件路径: "
    if "!INPUT!"=="" exit /b
) else (
    set "INPUT=%~1"
)

set /p "OUTPUT=输出目录（默认 split）: "
if "!OUTPUT!"=="" set "OUTPUT=split"

echo.
echo [*] 正在拆分: %INPUT%
python "%PY_SCRIPT%" split "%INPUT%" -o "%OUTPUT%"

echo.
pause
