@echo off
echo Starting DTG Workflow Automations Backend...
echo.
echo Make sure PostgreSQL is running: docker-compose up -d
echo.

cd /d "%~dp0"

REM Check if virtual environment exists
if not exist "venv" (
    echo Virtual environment not found. Creating...
    py -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate

REM Install dependencies if needed
echo Installing/updating dependencies...
pip install -r requirements.txt

REM Start the server
echo.
echo Starting FastAPI server...
echo Server will be available at: http://localhost:8000
echo API docs at: http://localhost:8000/docs
echo.
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
