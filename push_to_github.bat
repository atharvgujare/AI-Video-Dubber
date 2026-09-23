@echo off
title Push AI Dubber Studio to GitHub
cd /d "%~dp0"

echo ================================================================
echo           AI DUBBER STUDIO - GITHUB CLOUD SYNC
echo ================================================================
echo.

git --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Git is not installed or not in your PATH.
    echo Please install Git from https://git-scm.com/ or use GitHub Desktop.
    pause
    exit /b 1
)

if not exist ".git" (
    echo [+] Initializing local Git repository...
    git init
    git branch -M main
)

git remote get-url origin >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo.
    echo [!] No GitHub remote found.
    set /p REPO_URL="Enter your GitHub Repository URL (e.g. https://github.com/username/ai-dubber.git): "
    if "%REPO_URL%"=="" (
        echo [ERROR] No URL provided. Aborting.
        pause
        exit /b 1
    )
    git remote add origin %REPO_URL%
)

echo.
echo [+] Staging and committing files...
git add .
set /p COMMIT_MSG="Enter commit message (Press Enter for 'Update AI Dubber Studio'): "
if "%COMMIT_MSG%"=="" set COMMIT_MSG=Update AI Dubber Studio

git commit -m "%COMMIT_MSG%"

echo.
echo [+] Pushing to GitHub (main branch)...
git push -u origin main

if %ERRORLEVEL% equ 0 (
    echo.
    echo ================================================================
    echo [+] SUCCESS! Your code is live on GitHub!
    echo [+] Render.com will now automatically detect the update and deploy.
    echo ================================================================
) else (
    echo.
    echo [!] Push failed. Check your GitHub permissions or credentials.
)

echo.
pause
