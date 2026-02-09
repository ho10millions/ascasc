@echo off
chcp 65001 >nul
title Scrooge's Price Aggregator
echo.
echo  ===================================
echo   Scrooge's Price Aggregator
echo   Gaming Arbitrage Hunter
echo  ===================================
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found! Install Python from python.org
    pause
    exit /b 1
)

REM Install dependencies
echo [1/2] Installing dependencies...
pip install -r "%~dp0requirements.txt" --quiet 2>nul
if %errorlevel% neq 0 (
    echo [WARN] pip install had issues, trying with --break-system-packages...
    pip install -r "%~dp0requirements.txt" --quiet --break-system-packages 2>nul
)

echo [2/2] Starting server...
echo.
echo  ====================================
echo   Server starting at:
echo   http://localhost:8000
echo  ====================================
echo.
echo  Admin invite code: SCROOGE-ADMIN-2024
echo  (use it to register the first user)
echo.
echo  Press Ctrl+C to stop the server
echo  ====================================
echo.

cd /d "%~dp0backend"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

pause
