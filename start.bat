@echo off
setlocal enabledelayedexpansion

echo ========================================
echo   Image Processor - Windows Starter
echo ========================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo [INFO] Python found:
python --version
echo.

:: Navigate to script directory
cd /d "%~dp0"


:: Activate venv
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment.
    pause
    exit /b 1
)
echo [OK] Virtual environment activated.
echo.

:: Launch the server
echo ========================================
echo   Starting Image Processor
echo ========================================
echo.

python main.py

:: Deactivate venv on exit
call venv\Scripts\deactivate.bat 2>nul

pause
