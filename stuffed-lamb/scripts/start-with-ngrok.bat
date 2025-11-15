@echo off
REM ======================================
REM Stuffed Lamb Complete Startup - Windows
REM Starts: Redis (optional) + Application + ngrok
REM ======================================

echo.
echo ============================================
echo Stuffed Lamb VAPI Ordering System
echo Complete Startup (with ngrok tunnel)
echo ============================================
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
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Check for ngrok
where ngrok >nul 2>&1
if errorlevel 1 (
    echo [WARNING] ngrok not found!
    echo.
    echo For VAPI integration, you need ngrok to expose your local server.
    echo.
    echo Download from: https://ngrok.com/download
    echo After installing, add ngrok to your PATH
    echo.
    echo Alternatives:
    echo   1. Deploy to production (see PRODUCTION_DEPLOYMENT.md)
    echo   2. Use cloudflared tunnel
    echo   3. Deploy to cloud and skip ngrok
    echo.
    set /p CONTINUE="Continue without ngrok? (y/N): "
    if /i not "%CONTINUE%"=="y" (
        echo.
        echo Exiting. Please install ngrok or deploy to production.
        pause
        exit /b 1
    )
    set NGROK_AVAILABLE=0
) else (
    set NGROK_AVAILABLE=1
    echo [INFO] ngrok found
)

REM Check if virtual environment exists
if exist venv\Scripts\activate.bat (
    echo [INFO] Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo [WARNING] Virtual environment not found
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

REM Check for Redis (optional)
echo.
echo [INFO] Checking for Redis...
where redis-server >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Redis not found - using in-memory sessions
    echo [INFO] For production, install Redis:
    echo [INFO]   - Download from: https://github.com/microsoftarchive/redis/releases
    echo [INFO]   - Or use Docker: docker run -d -p 6379:6379 redis:alpine
) else (
    echo [INFO] Starting Redis...
    start "Stuffed Lamb Redis" redis-server
    timeout /t 2 /nobreak >nul
)

REM Start the application server in background
echo.
echo [INFO] Starting Stuffed Lamb application server...
start "Stuffed Lamb Server" python run.py

REM Wait for server to start
echo [INFO] Waiting for server to start...
timeout /t 5 /nobreak >nul

REM Check if server is running
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Server health check failed
    echo [INFO] Server might still be starting...
) else (
    echo [SUCCESS] Server is running on http://localhost:8000
)

REM Start ngrok if available
if %NGROK_AVAILABLE%==1 (
    echo.
    echo [INFO] Starting ngrok tunnel...
    start "Stuffed Lamb ngrok" ngrok http 8000

    echo.
    echo ============================================
    echo SUCCESS! All services started
    echo ============================================
    echo.
    echo Application:  http://localhost:8000
    echo Health Check: http://localhost:8000/health
    echo.
    echo NGROK TUNNEL:
    echo   1. Check the ngrok window for your public URL
    echo   2. It will look like: https://xxxx-xx-xxx.ngrok-free.app
    echo   3. Use this URL in VAPI webhook settings
    echo   4. Set VAPI webhook to: https://your-ngrok-url/vapi/webhook
    echo.
    echo Ngrok Dashboard: http://localhost:4040
    echo.
) else (
    echo.
    echo ============================================
    echo Server started (without ngrok)
    echo ============================================
    echo.
    echo Application:  http://localhost:8000
    echo Health Check: http://localhost:8000/health
    echo.
    echo [WARNING] VAPI integration will NOT work without public URL
    echo [INFO] Install ngrok or deploy to production
    echo.
)

echo Press any key to view logs, or close this window to keep services running...
pause >nul

REM Show server logs
echo.
echo Showing server logs (Ctrl+C to exit)...
timeout /t 2 /nobreak >nul

REM Note: Since we started server in a new window, we can't tail logs here
echo [INFO] Check the "Stuffed Lamb Server" window for logs
echo.

pause
