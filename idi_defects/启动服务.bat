@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ========================================
echo   IDI 缺陷速查 - 用户认证服务
echo ========================================
echo.

REM 获取本机局域网IP
for /f "tokens=2 delims=[]" %%a in ('ping -4 -n 1 %computername% ^| findstr "["') do (
    set LOCAL_IP=%%a
    goto :found
)
:found

if defined LOCAL_IP (
    echo 访问地址:
    echo   本机:   http://localhost:5173
    echo   局域网: http://%LOCAL_IP%:5173
    echo   公网:   用 cpolar / localtunnel 暴露
) else (
    echo 访问地址: http://localhost:5173
)
echo.
echo 按 Ctrl+C 停止服务
echo ========================================
echo.

python auth_server.py

pause
