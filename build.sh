#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "========================================="
echo "   AI DUBBER STUDIO - RENDER CLOUD BUILD"
echo "========================================="

# 1. Install Python dependencies
echo "[+] Installing Python backend dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt

# 2. Build React Frontend
echo "[+] Building React Vite frontend..."
cd frontend
npm install
npm run build
cd ..

echo "========================================="
echo "   BUILD COMPLETED SUCCESSFULLY!"
echo "========================================="
