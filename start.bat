@echo off
setlocal

title TransitNotice (WEB-07: Tamil Nadu Public Transport Service Update Tracker)
cd /d "%~dp0"

echo ===============================================================================
echo        TransitNotice - Tamil Nadu Public Transport Service Update Tracker
echo        Flask + SQLite Backend  ^|  React + Tailwind Minimalist Frontend
echo ===============================================================================
echo.

:: 1. Check Python installation
set "PYTHON_EXE="
where python >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_EXE=python"
) else (
    where py >nul 2>&1
    if %errorlevel% equ 0 (
        set "PYTHON_EXE=py"
    )
)

if "%PYTHON_EXE%"=="" (
    echo [ERROR] Neither python nor py was found in system PATH.
    echo Please install Python 3.10 or higher.
    pause
    exit /b 1
)

echo [OK] Python runtime: %PYTHON_EXE%

:: 2. Check & install backend dependencies
%PYTHON_EXE% -c "import flask, flask_cors" >nul 2>&1
if %errorlevel% neq 0 (
    echo [*] Installing Flask and dependencies...
    %PYTHON_EXE% -m pip install -r backend\requirements.txt --disable-pip-version-check
    echo [OK] Backend dependencies installed.
) else (
    echo [OK] Backend dependencies verified.
)

:: 3. Initialize database schema
echo [*] Initializing database schema...
%PYTHON_EXE% -c "from backend.db import init_db; init_db()" >nul 2>&1
echo [OK] Database schema initialized.

:: 4. Verify frontend production build
if not exist "frontend\dist\index.html" (
    echo [*] Building React frontend bundle...
    cd frontend
    call npm run build
    cd ..
    echo [OK] Frontend build complete.
) else (
    echo [OK] Frontend production bundle detected.
)

echo.
echo ===============================================================================
echo  TransitNotice is running! Access the application routes below:
echo.
echo   - Web Application Dashboard: http://127.0.0.1:5000/
echo   - Current Notices          : http://127.0.0.1:5000/
echo   - Ended Notices            : http://127.0.0.1:5000/ended
echo   - Get Alerts               : http://127.0.0.1:5000/alerts
echo   - Data Sources ^& Health   : http://127.0.0.1:5000/sources
echo.
echo   - Demo Metro HTML Source   : http://127.0.0.1:5000/demo-source/metro
echo   - Demo Private Coaches RSS : http://127.0.0.1:5000/demo-source/private_coaches.xml
echo.
echo  Press Ctrl+C in this terminal window to stop the server.
echo ===============================================================================
echo.

:: 5. Launch Flask application
%PYTHON_EXE% -m backend.app

echo.
echo [INFO] TransitNotice server has stopped.
pause
