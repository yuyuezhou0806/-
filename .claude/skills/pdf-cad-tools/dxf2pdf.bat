@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"
set "PY_SCRIPT=%SCRIPT_DIR%cad_to_pdf.py"

if "%~1"=="" (
    echo ========================================
    echo   DXF to PDF 转换工具
echo ========================================
    echo.
    echo 用法:
    echo   1. 把 .dxf 文件拖到这个图标上（支持多文件）
    echo   2. 或双击运行后输入文件路径
echo.
    set /p "INPUT=请输入 DXF 文件路径（或 *.dxf）: "
    if "!INPUT!"=="" exit /b
) else (
    set "INPUT=%~1"
)

echo.
echo [*] 正在转换: %INPUT%
python "%PY_SCRIPT%" "%INPUT%"

echo.
pause
