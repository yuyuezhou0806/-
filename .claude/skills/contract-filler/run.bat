@echo off
chcp 65001 >nul
echo ========================================
echo      合同自动填充工具
echo ========================================
echo.

set "SCRIPT_DIR=%~dp0"
set "PY_SCRIPT=%SCRIPT_DIR%contract_filler.py"

if "%~1"=="" (
    set "CONFIG=%SCRIPT_DIR%config.json"
    echo 使用默认配置文件: config.json
) else (
    set "CONFIG=%~1"
    echo 使用配置文件: %CONFIG%
)

if not exist "%CONFIG%" (
    echo [X] 配置文件不存在: %CONFIG%
    pause
    exit /b 1
)

echo.
echo [*] 正在填充合同...
python "%PY_SCRIPT%" "%CONFIG%"

echo.
pause