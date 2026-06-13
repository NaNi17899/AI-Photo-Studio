# Setup Guide

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| OS | Windows 10 / Ubuntu 20.04 | Windows 11 / Ubuntu 22.04 |
| GPU | NVIDIA GTX 1650 (4GB) | RTX 3060+ (8GB+) |
| CPU | 4-core | 6-core+ |
| RAM | 8 GB | 16 GB+ |
| Disk | 10 GB free | 30 GB+ |
| Python | 3.10 | 3.10-3.12 |
| Node.js | 18 | 20+ |

## Step-by-Step Setup (Windows)

### 1. Prerequisites

1. Install [Python 3.10+](https://www.python.org/downloads/)
   - ✅ Check "Add Python to PATH"
2. Install [Node.js 18+](https://nodejs.org/)
3. Install [NVIDIA CUDA Toolkit 11.8](https://developer.nvidia.com/cuda-11-8-0-download-archive)
4. Update GPU drivers to latest version

### 2. Verify Setup
```bash
python --version   # Should show 3.10+
node --version     # Should show 18+
nvidia-smi         # Should show GPU info
```

### 3. Install
```bash
cd ai_photo_studio
scripts\install.bat
```

This will:
- Create a Python virtual environment
- Install PyTorch with CUDA 11.8
- Install all Python dependencies
- Install React frontend dependencies
- Build the frontend

### 4. Download Models
```bash
venv\Scripts\activate
python scripts\download_models.py
```

Downloads ~500MB of core models (GFPGAN, Real-ESRGAN).
Optional models (CodeFormer, anime) are downloaded on demand.

### 5. Start
```bash
scripts\start.bat
```

Open http://127.0.0.1:8000 in your browser.

## Troubleshooting

### "CUDA not available"
- Ensure NVIDIA drivers are up to date
- Verify CUDA toolkit is installed: `nvcc --version`
- Reinstall PyTorch: `pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118`

### "Out of memory"
- Close other GPU-heavy applications
- Reduce tile size in Settings
- The app auto-falls back to CPU for OOM errors

### "Module not found"
- Ensure virtual environment is activated: `venv\Scripts\activate`
- Reinstall: `pip install -r requirements.txt`

### Frontend not loading
- Build frontend: `cd frontend && npm run build`
- Or run dev server: `cd frontend && npm run dev` (separate terminal)
