@echo off
echo ============================================
echo  AI Photo Studio - Installing All Packages
echo ============================================
echo.

echo [1/6] Upgrading pip...
python -m pip install --upgrade pip

echo.
echo [2/6] Installing PyTorch with CUDA 11.8...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

echo.
echo [3/6] Installing background removal...
pip install rembg[gpu] Pillow

echo.
echo [4/6] Installing face enhancement...
pip install gfpgan basicsr facexlib realesrgan

echo.
echo [5/6] Installing inpainting (LaMa)...
pip install simple-lama-inpainting

echo.
echo [6/6] Installing UI and utilities...
pip install gradio==4.44.0 opencv-python numpy requests tqdm

echo.
echo ============================================
echo  All packages installed successfully
echo  Now run: python step3_download_models.py
echo ============================================
pause
