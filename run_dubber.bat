@echo off
title YouTube AI Dubber
cd /d "%~dp0"

echo ================================================================
echo               YOUTUBE AI DUBBER - SELECT LAUNCH MODE
echo ================================================================
echo.
echo  [1] Launch Web Studio (Modern React Dashboard - Recommended)
echo  [2] Run Command-Line Dubber (CLI)
echo  [3] Run Automated Verification Tests
echo  [4] Exit
echo.
set /p mode="Enter choice [1-4] (default: 1): "

if "%mode%"=="" set mode=1
if "%mode%"=="1" (
    call start_studio.bat
    exit /b
)
if "%mode%"=="2" (
    call .venv\Scripts\activate.bat
    echo.
    set /p url="Enter YouTube URL or video path: "
    set /p lang="Enter Target Language code (hi/mr/ta/te/bn/gu/kn/ml/pa/ur/en/es/fr/de/ja - default: hi): "
    if "%lang%"=="" set lang=hi
    python dub_video.py "%url%" --language %lang%
    pause
    exit /b
)
if "%mode%"=="3" (
    call .venv\Scripts\activate.bat
    python backend\test_pipeline.py
    pause
    exit /b
)
exit /b
