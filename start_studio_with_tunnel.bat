@echo off
title AI Dubber Studio - Cloudflare Mobile Tunnel Launcher
cd /d "%~dp0"

echo ================================================================
echo        AI DUBBER STUDIO - MOBILE TUNNEL LAUNCHER
echo ================================================================
echo.
echo [+] Launching local server and Cloudflare Public Tunnel...
echo [+] This gives you a secure, free HTTPS public link for your phone!
echo [+] Since it runs through your home connection, YouTube link
echo     downloads WORK 100%% WITH NO BOT BLOCKS AND NO COOKIES!
echo.

if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found in .venv.
    pause
    exit /b 1
)

if not exist "cloudflared.exe" (
    echo [ERROR] cloudflared.exe not found in this folder.
    pause
    exit /b 1
)

:: Start backend in a separate background window
start "AI Dubber Backend Engine" cmd /c "call .venv\Scripts\activate.bat && python -m uvicorn backend.server:app --host 127.0.0.1 --port 8000"

echo [+] Waiting 3 seconds for engine to start...
timeout /t 3 /nobreak >nul

echo.
echo ================================================================
echo   CONNECTING TO CLOUDFLARE PUBLIC TUNNEL (HTTPS)
echo   Look for the URL below ending in '.trycloudflare.com'
echo   Open that URL on your mobile phone browser to dub videos!
echo ================================================================
echo.

.\cloudflared.exe tunnel --url http://127.0.0.1:8000

pause
