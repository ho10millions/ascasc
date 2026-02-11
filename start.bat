@echo off
chcp 65001 >nul
title Mammonia — Gaming Arbitrage
echo.
echo  ===================================
echo   Mammonia - Gaming Arbitrage
echo  ===================================
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found! Install Python from python.org
    pause
    exit /b 1
)

REM Check Node
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found! Install from nodejs.org
    pause
    exit /b 1
)

REM Install Python dependencies
echo [1/4] Installing Python dependencies...
pip install -r "%~dp0requirements.txt" --quiet 2>nul
pip install aiosqlite --quiet 2>nul

REM Install frontend dependencies
echo [2/4] Installing frontend dependencies...
cd /d "%~dp0frontend"
call npm install --silent 2>nul

REM Build frontend
echo [3/4] Building frontend...
call npm run build
if %errorlevel% neq 0 (
    echo [ERROR] Frontend build failed!
    pause
    exit /b 1
)

echo [4/4] Starting server...
echo.
echo  ====================================
echo   Mammonia running at:
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
