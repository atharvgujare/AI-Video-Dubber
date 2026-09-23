#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "========================================="
echo "   AI DUBBER STUDIO - RENDER CLOUD BUILD"
echo "========================================="

# 1. Install Deno JS runtime for yt-dlp challenge solving
if ! command -v deno &> /dev/null; then
    echo "[+] Installing Deno JS runtime for YouTube challenge solving..."
    curl -fsSL https://deno.land/install.sh | sh || true
    export DENO_INSTALL="$HOME/.deno"
    export PATH="$DENO_INSTALL/bin:$PATH"
fi

# 2. Install Python dependencies
echo "[+] Installing Python backend dependencies..."
pip install -r requirements.txt
pip install --upgrade yt-dlp yt-dlp-ejs

# 2. Build React Frontend
echo "[+] Building React Vite frontend..."
cd frontend
npm install
npm run build
cd ..

echo "========================================="
echo "   BUILD COMPLETED SUCCESSFULLY!"
echo "========================================="
