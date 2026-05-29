@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo  合同生成器 Web 服务
echo ========================================
echo.

REM 解析本机内网 IP(取第一个 192/10/172 开头的 IPv4)
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /R "IPv4"') do (
    for /f "tokens=*" %%b in ("%%a") do (
        echo %%b | findstr /R "^ \(192\.\|10\.\|172\.\)" >nul && (
            set "LANIP=%%b"
            goto :ipfound
        )
    )
)
:ipfound

set "LANIP=%LANIP: =%"

echo  本机: http://localhost:8000
if defined LANIP (
    echo  内网: http://%LANIP%:8000
    echo.
    echo  公司同事在浏览器打开上面"内网"那个地址即可使用
) else (
    echo  ^(未检测到内网 IP,只能在本机访问^)
)
echo.
echo  关闭此窗口即可停止服务
echo ========================================
echo.

REM 启动 uvicorn,绑 0.0.0.0 让局域网能访问
"..\.venv\Scripts\python.exe" -m uvicorn main:app --host 0.0.0.0 --port 8000

pause
