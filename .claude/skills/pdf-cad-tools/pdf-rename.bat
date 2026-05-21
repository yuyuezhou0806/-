@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "PY_SCRIPT=%SCRIPT_DIR%pdf_tools.py"

echo ========================================
echo   PDF 批量重命名工具
echo ========================================
echo.

set /p "FOLDER=目标文件夹（默认当前目录）: "
if "!FOLDER!"=="" set "FOLDER=."

echo.
echo 正则替换示例:
echo   模式: ^old_        替换: new_       效果: old_file.pdf → new_file.pdf
echo   模式: ^\d+_         替换: （空）      效果: 001_report.pdf → report.pdf
echo   模式: report        替换: document    效果: report_A.pdf → document_A.pdf
echo.

set /p "PATTERN=匹配模式（正则）: "
if "!PATTERN!"=="" (
    echo [X] 模式不能为空
    pause
    exit /b
)

set /p "REPLACEMENT=替换为: "

echo.
echo [*] 预览模式（不实际执行）:
python "%PY_SCRIPT%" rename "%PATTERN%" "%REPLACEMENT%" -d "%FOLDER%" --dry-run

echo.
set /p "CONFIRM=确认执行? [y/N]: "
if /i "!CONFIRM!"=="y" (
    echo.
    python "%PY_SCRIPT%" rename "%PATTERN%" "%REPLACEMENT%" -d "%FOLDER%"
) else (
    echo [X] 已取消
)

echo.
pause
