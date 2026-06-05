@echo off
echo Starting FocusPilot Frontend...
echo.

REM Navigate to script directory
cd /d "%~dp0"

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo Error: Node.js is not installed or not in PATH
    echo Please download from https://nodejs.org/
    pause
    exit /b 1
)

cd frontend

REM Install dependencies if needed
if not exist "node_modules" (
    echo Installing Node.js dependencies...
    npm install
)

echo Starting frontend on http://localhost:5173...
echo Open http://localhost:5173 in your browser
echo.
echo Make sure the backend is running on port 8765 first!
echo.
npm run dev

pause
