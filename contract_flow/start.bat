@echo off

for /f "tokens=2 delims=: " %%a in ('ipconfig ^| findstr /i "IPv4"') do (
    set LAN_IP=%%a
)
set LAN_IP=%LAN_IP: =%

echo =========================================
echo     He Tong Liu Zhuan Xi Tong
echo =========================================
echo.
echo Local:   http://127.0.0.1:8001
echo Network: http://%LAN_IP%:8001
echo.
echo Press Ctrl+C to stop
echo =========================================
echo.

cd /d "%~dp0"
python -m uvicorn main:app --host 0.0.0.0 --port 8001

pause
