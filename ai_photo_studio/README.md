# AI Photo Studio v2.0

Professional AI photo editing platform — powered by GFPGAN, Real-ESRGAN, Stable Diffusion, LaMa, and more.

## Features

| Feature | Models | VRAM |
|---------|--------|------|
| ✂️ Background Removal | rembg (U2NET) | 300 MB |
| ✨ Face Enhancement | GFPGAN v1.4, CodeFormer | 500 MB |
| 🔍 Image Upscaling | Real-ESRGAN 2x/4x/8x | 400 MB |
| 🧹 Object Removal | LaMa Inpainting | 300 MB |
| 🔤 Watermark Removal | EasyOCR + LaMa | 400 MB |
| 🎨 Color Grading | Pure NumPy/PIL | 0 MB |
| 🎭 Style Transfer | Stable Diffusion 1.5 + LoRA | 3500 MB |
| 🎌 Cartoon & Anime | CV2/SD + anime LoRA | 0-3500 MB |
| 👔 AI Headshots | GFPGAN + rembg pipeline | 800 MB |
| 💒 Wedding Studio | Batch pipeline orchestrator | varies |

## Architecture

- **Backend**: FastAPI + async job queue + WebSocket progress
- **Frontend**: React + Vite with dark glassmorphism UI
- **AI Engine**: Plugin-based with VRAM-aware model management
- **Database**: SQLite for job history and presets
- **GPU**: Optimized for GTX 1650 (4GB VRAM) with LRU eviction

## Quick Start

### 1. Install
```bash
# Windows
scripts\install.bat

# Or manually:
python -m venv venv
venv\Scripts\activate
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install -r requirements.txt
cd frontend && npm install && npm run build && cd ..
```

### 2. Download Models
```bash
python scripts/download_models.py
```

### 3. Start
```bash
# Windows
scripts\start.bat

# Or manually:
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000 in your browser.

### Development Mode
```bash
# Terminal 1: Backend
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2: Frontend (hot reload)
cd frontend && npm run dev
```

## Docker

```bash
cd docker
docker-compose up --build
```

Requires NVIDIA Container Toolkit for GPU support.

## API Documentation

Auto-generated API docs available at:
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Project Structure

```
ai_photo_studio/
├── backend/           # FastAPI application
│   ├── main.py        # App entry point
│   ├── config.py      # Settings & model registry
│   ├── database.py    # SQLite + SQLAlchemy
│   ├── api/           # REST API routers
│   ├── core/          # Model manager, job queue, plugin system
│   ├── plugins/       # 10 AI feature plugins
│   └── storage/       # File management
├── frontend/          # React + Vite SPA
│   ├── src/
│   │   ├── components/  # Reusable UI components
│   │   ├── pages/       # Feature pages
│   │   ├── api/         # API client
│   │   └── hooks/       # WebSocket hooks
│   └── dist/            # Production build
├── data/              # Runtime data (models, uploads, outputs)
├── scripts/           # Install, download, start scripts
├── docker/            # Docker configuration
└── docs/              # Documentation
```

## Hardware Requirements

- **GPU**: NVIDIA GTX 1650 (4GB VRAM) or better
- **CPU**: AMD Ryzen 5 4600H or equivalent
- **RAM**: 16GB recommended
- **Disk**: 15GB for models + workspace
- **OS**: Windows 10/11, Linux
- **Python**: 3.10+

## License

For personal and commercial use.
