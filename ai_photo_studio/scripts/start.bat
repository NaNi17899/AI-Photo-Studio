@echo off
echo ============================================================
echo  AI Photo Studio v2.0 — Starting...
echo ============================================================

REM Activate virtual environment
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo WARNING: Virtual environment not found. Run scripts\install.bat first.
)

REM Copy .env if not exists
if not exist ".env" (
    if exist ".env.example" (
        copy .env.example .env
        echo Created .env from .env.example
    )
)

echo.
echo Starting FastAPI backend on http://127.0.0.1:8000
echo API docs at http://127.0.0.1:8000/docs
echo.

REM Check if frontend build exists
if exist "frontend\dist\index.html" (
    echo Frontend: Serving built files from frontend/dist/
    echo Open http://127.0.0.1:8000 in your browser
) else (
    echo Frontend: No build found. Run 'cd frontend && npm run dev' separately
    echo Or build with 'cd frontend && npm run build'
    echo API available at http://127.0.0.1:8000/docs
)

echo.
echo ============================================================

python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

pause
