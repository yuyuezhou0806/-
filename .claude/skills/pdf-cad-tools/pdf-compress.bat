@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "PY_SCRIPT=%SCRIPT_DIR%pdf_tools.py"

if "%~1"=="" (
    echo ========================================
    echo   PDF 压缩工具
    echo ========================================
    echo.
    echo 用法:
    echo   把 .pdf 文件拖到这个图标上
    echo.
    echo 压缩模式:
    echo   low    - 高压缩，画质较低（适合预览）
    echo   medium - 中等压缩，平衡画质（默认）
    echo   high   - 低压缩，画质较好
    echo.
    set /p "INPUT=请输入 PDF 文件路径: "
    if "!INPUT!"=="" exit /b
) else (
    set "INPUT=%~1"
)

echo.
echo 请选择压缩质量:
echo   1 - low    (高压缩)
echo   2 - medium (中等压缩, 默认)
echo   3 - high   (低压缩)
set /p "QUALITY_CHOICE=输入数字 [1-3, 默认2]: "

if "!QUALITY_CHOICE!"=="1" (
    set "QUALITY=low"
) else if "!QUALITY_CHOICE!"=="3" (
    set "QUALITY=high"
) else (
    set "QUALITY=medium"
)

echo.
echo [*] 正在压缩: %INPUT% (质量: %QUALITY%)
python "%PY_SCRIPT%" compress "%INPUT%" --quality %QUALITY%

echo.
pause
