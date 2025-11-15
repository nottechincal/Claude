@echo off
REM ======================================
REM Stuffed Lamb Server - Windows Startup Script
REM ======================================

echo.
echo ====================================
echo Stuffed Lamb VAPI Ordering System
echo Starting server...
echo ====================================
echo.

REM Check if .env file exists
if not exist .env (
    echo [ERROR] .env file not found!
    echo.
    echo Please create .env file:
    echo   1. Copy .env.example to .env
    echo   2. Edit .env with your Twilio credentials
    echo   3. Update SHOP_ORDER_TO with shop phone number
    echo.
    pause
    exit /b 1
)

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo Please install Python 3.8 or higher from https://python.org
    pause
    exit /b 1
)

REM Check if virtual environment exists
if exist venv\Scripts\activate.bat (
    echo [INFO] Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo [WARNING] Virtual environment not found at venv\
    echo [INFO] Using system Python...
)

REM Install/update dependencies
echo [INFO] Checking dependencies...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

REM Run the server
echo.
echo [INFO] Starting Stuffed Lamb server...
echo [INFO] Press Ctrl+C to stop
echo.
python run.py

REM If server exits, pause to show any error messages
if errorlevel 1 (
    echo.
    echo [ERROR] Server exited with error
    pause
)
