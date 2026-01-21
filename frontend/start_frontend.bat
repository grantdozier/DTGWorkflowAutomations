@echo off
echo Starting DTG Workflow Automations Frontend...
echo.
echo Make sure backend is running on port 8000
echo.

cd /d "%~dp0"

REM Check if node_modules exists
if not exist "node_modules" (
    echo Installing dependencies...
    npm install
)

echo.
echo Starting development server...
echo Frontend will be available at: http://localhost:5173
echo.
npm run dev
