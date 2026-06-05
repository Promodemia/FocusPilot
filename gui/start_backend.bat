@echo off
echo Starting FocusPilot Backend...
echo.

REM Navigate to script directory
cd /d "%~dp0"

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo Virtual environment not found. Creating...
    python -m venv venv
    call venv\Scripts\activate.bat
    cd backend
    pip install -r requirements.txt
    cd ..
) else (
    REM Activate virtual environment
    call venv\Scripts\activate.bat
)

echo Starting backend on http://0.0.0.0:8765...
cd backend
python main.py

pause
