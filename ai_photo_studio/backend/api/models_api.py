"""
Model management API — download, status, VRAM monitoring.
"""

import logging
import threading
import urllib.request
from fastapi import APIRouter, HTTPException

from backend.config import get_settings, MODEL_REGISTRY
from backend.core.model_manager import get_model_manager
from backend.core.gpu_utils import get_gpu_info, get_vram_free_mb, get_vram_used_mb

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/models", tags=["models"])

# Track download progress
_download_progress: dict[str, dict] = {}


@router.get("")
async def list_models():
    """List all models with download and load status."""
    settings = get_settings()
    mm = get_model_manager()
    model_status = mm.get_status()

    models = []
    for name, entry in MODEL_REGISTRY.items():
        model_path = settings.storage.models_dir / entry.filename
        downloaded = model_path.exists()
        file_size_mb = round(model_path.stat().st_size / 1024**2, 1) if downloaded else 0

        status_info = model_status.get(name, {})

        models.append(
            {
                "name": name,
                "filename": entry.filename,
                "description": entry.description,
                "size_mb": entry.size_mb,
                "vram_mb": entry.vram_mb,
                "required": entry.required,
                "downloaded": downloaded,
                "file_size_mb": file_size_mb,
                "load_state": status_info.get("state", "unloaded"),
                "load_count": status_info.get("load_count", 0),
                "download_progress": _download_progress.get(name, None),
            }
        )

    return {"models": models}


@router.post("/{model_name}/download")
async def download_model(model_name: str):
    """Trigger model download."""
    if model_name not in MODEL_REGISTRY:
        raise HTTPException(404, f"Unknown model: {model_name}")

    entry = MODEL_REGISTRY[model_name]
    settings = get_settings()
    dest = settings.storage.models_dir / entry.filename

    if dest.exists():
        return {"message": "Model already downloaded", "path": str(dest)}

    # Download in background thread
    if model_name in _download_progress:
        return {"message": "Download already in progress"}

    def _download():
        try:
            _download_progress[model_name] = {"percent": 0, "status": "downloading"}

            def progress(count, block_size, total_size):
                if total_size > 0:
                    pct = int(count * block_size * 100 / total_size)
                    _download_progress[model_name] = {
                        "percent": min(pct, 100),
                        "status": "downloading",
                        "downloaded_mb": round(count * block_size / 1024**2, 1),
                        "total_mb": round(total_size / 1024**2, 1),
                    }

            urllib.request.urlretrieve(entry.url, str(dest), progress)
            _download_progress[model_name] = {"percent": 100, "status": "completed"}
            logger.info("Model '%s' downloaded to %s", model_name, dest)
        except Exception as e:
            _download_progress[model_name] = {"percent": 0, "status": "failed", "error": str(e)}
            logger.error("Failed to download '%s': %s", model_name, e)
            if dest.exists():
                dest.unlink()  # Remove partial download

    thread = threading.Thread(target=_download, daemon=True)
    thread.start()

    return {"message": "Download started", "model": model_name}


@router.get("/{model_name}/download-progress")
async def get_download_progress(model_name: str):
    """Get download progress for a model."""
    progress = _download_progress.get(model_name)
    if not progress:
        return {"status": "not_started"}
    return progress


@router.delete("/{model_name}")
async def delete_model(model_name: str):
    """Delete a downloaded model."""
    if model_name not in MODEL_REGISTRY:
        raise HTTPException(404, f"Unknown model: {model_name}")

    entry = MODEL_REGISTRY[model_name]
    settings = get_settings()
    path = settings.storage.models_dir / entry.filename

    # Unload first if loaded
    mm = get_model_manager()
    mm.unload_sync(model_name)

    if path.exists():
        path.unlink()
        return {"message": f"Model '{model_name}' deleted"}
    else:
        raise HTTPException(404, "Model file not found")


@router.post("/{model_name}/unload")
async def unload_model(model_name: str):
    """Unload a model from GPU memory."""
    mm = get_model_manager()
    await mm.unload(model_name)
    return {"message": f"Model '{model_name}' unloaded"}


@router.post("/unload-all")
async def unload_all_models():
    """Unload all models — emergency VRAM cleanup."""
    mm = get_model_manager()
    await mm.unload_all()
    return {"message": "All models unloaded", "vram_free_mb": round(get_vram_free_mb(), 1)}


@router.get("/vram")
async def get_vram_status():
    """Get current VRAM usage."""
    return {
        "gpu_info": get_gpu_info(),
        "vram_used_mb": round(get_vram_used_mb(), 1),
        "vram_free_mb": round(get_vram_free_mb(), 1),
        "loaded_models": get_model_manager().get_loaded_models(),
        "estimated_model_vram_mb": get_model_manager().get_total_vram_used_by_models(),
    }
