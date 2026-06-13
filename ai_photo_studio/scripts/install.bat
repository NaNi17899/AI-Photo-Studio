@echo off
echo ============================================================
echo  AI Photo Studio v2.0 — Installation Script
echo ============================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.10+ from python.org
    pause
    exit /b 1
)

echo [1/5] Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo     Virtual environment created.
) else (
    echo     Virtual environment already exists.
)

echo.
echo [2/5] Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo [3/5] Installing PyTorch with CUDA 11.8...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

echo.
echo [4/5] Installing Python dependencies...
pip install -r requirements.txt

echo.
echo [5/5] Installing frontend dependencies and building...
cd frontend
call npm install
call npm run build
cd ..

echo.
echo ============================================================
echo  Installation complete!
echo.
echo  Copy .env.example to .env and customize if needed:
echo    copy .env.example .env
echo.
echo  Download core models:
echo    python scripts\download_models.py
echo.
echo  Start the application:
echo    scripts\start.bat
echo ============================================================
pause
