@echo off
cd /d "%~dp0"

call ..\.venv\Scripts\activate.bat

echo ========================================
echo  Starting subsidy system on port 8008
echo ========================================

echo [1/2] Starting uvicorn server...
start "uvicorn-server" ..\.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8008

echo [2/2] Waiting...
timeout /t 3 /nobreak > nul

echo.
echo Server started!
echo Open browser: http://localhost:8008
echo.
pause
