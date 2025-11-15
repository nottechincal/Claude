@echo off
REM ======================================
REM Stuffed Lamb - Stop All Services (Windows)
REM ======================================

echo.
echo ====================================
echo Stopping Stuffed Lamb Services
echo ====================================
echo.

REM Stop Python processes
echo [INFO] Stopping Stuffed Lamb server...
taskkill /FI "WINDOWTITLE eq Stuffed Lamb Server" /F >nul 2>&1
if errorlevel 1 (
    echo [INFO] Server window not found, trying by process name...
    for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq python.exe" /NH ^| findstr "python.exe"') do (
        taskkill /PID %%i /F >nul 2>&1
    )
)

REM Stop ngrok
echo [INFO] Stopping ngrok...
taskkill /FI "WINDOWTITLE eq Stuffed Lamb ngrok" /F >nul 2>&1
taskkill /IM ngrok.exe /F >nul 2>&1

REM Stop Redis
echo [INFO] Stopping Redis...
taskkill /FI "WINDOWTITLE eq Stuffed Lamb Redis" /F >nul 2>&1
taskkill /IM redis-server.exe /F >nul 2>&1

echo.
echo [SUCCESS] All services stopped
echo.

pause
