@echo off
title AI Dubber Studio - Enterprise Multi-Lingual Suite
cd /d "%~dp0"

echo ================================================================
echo               AI DUBBER STUDIO - STARTING ENGINE
echo ================================================================
echo.

if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found in .venv.
    echo Please create the virtual environment first.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

netstat -ano | findstr :8000 | findstr LISTENING >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [+] Studio server is ALREADY ACTIVE and running on http://localhost:8000!
    echo [+] Opening web dashboard in your browser...
    start "" http://localhost:8000
    echo.
    echo The server is already live. You can use the web interface on PC or smartphone.
    echo Press any key to close this launcher window...
    pause >nul
    exit /b 0
)

echo [+] Starting FastAPI Engine and React Studio on http://localhost:8000 ...
echo [+] Accessible from any smartphone or tablet on your Wi-Fi!
echo [+] Press Ctrl+C in this terminal to stop the server.
echo.

start "" http://localhost:8000

python -m uvicorn backend.server:app --host 0.0.0.0 --port 8000

pause
