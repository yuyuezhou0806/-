@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "PY_SCRIPT=%SCRIPT_DIR%pdf_tools.py"

echo ========================================
echo   PDF 合并工具
echo ========================================
echo.

if "%~1"=="" (
    echo 用法:
    echo   把多个 PDF 文件拖到这个图标上，会自动合并
    echo.
    echo 或手动输入文件路径（用空格分隔）:
    set /p "FILES=PDF 文件路径: "
    if "!FILES!"=="" exit /b
) else (
    :: 收集所有拖放的文件
    set "FILES="
    :loop
    if "%~1"=="" goto done
    set "FILES=!FILES! "%~1""
    shift
    goto loop
    :done
)

set /p "OUTPUT=输出文件名（默认 merged.pdf）: "
if "!OUTPUT!"=="" set "OUTPUT=merged.pdf"

echo.
echo 是否生成合并报告?
echo   1 - 生成报告 (Excel + 文本)
echo   2 - 不生成报告
echo   默认: 不生成
set /p "REPORT=输入数字 [1-2, 默认2]: "

if "!REPORT!"=="1" (
    set "REPORT_FLAG=--report"
    echo [*] 将生成合并报告
) else (
    set "REPORT_FLAG="
)

echo.
echo [*] 正在合并...
python "%PY_SCRIPT%" merge %FILES% -o "%OUTPUT%" %REPORT_FLAG%

echo.
pause
