"""
Settings API endpoints.
"""

import logging
from fastapi import APIRouter

from backend.config import get_settings
from backend.storage.file_manager import get_file_manager
from backend.core.gpu_utils import get_gpu_info

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("")
async def get_app_settings():
    """Get current application settings."""
    settings = get_settings()
    fm = get_file_manager()
    return {
        "app_name": settings.app_name,
        "version": settings.version,
        "gpu": {
            "device": settings.gpu.device,
            "max_vram_usage_mb": settings.gpu.max_vram_mb
            if hasattr(settings.gpu, "max_vram_mb")
            else settings.gpu.max_vram_usage_mb,
            "mixed_precision": settings.gpu.mixed_precision,
            "tile_size": settings.gpu.tile_size,
            "idle_unload_seconds": settings.gpu.idle_unload_seconds,
        },
        "storage": {
            "uploads_dir": str(settings.storage.uploads_dir),
            "outputs_dir": str(settings.storage.outputs_dir),
            "models_dir": str(settings.storage.models_dir),
            "max_upload_size_mb": settings.storage.max_upload_size_mb,
            "disk_usage": fm.get_disk_usage(),
        },
        "server": {
            "host": settings.server.host,
            "port": settings.server.port,
            "debug": settings.server.debug,
        },
    }


@router.get("/system")
async def get_system_info():
    """Get system information (CPU, GPU, memory, disk)."""
    import platform
    import psutil

    cpu_info = {
        "processor": platform.processor(),
        "cores_physical": psutil.cpu_count(logical=False),
        "cores_logical": psutil.cpu_count(logical=True),
        "usage_percent": psutil.cpu_percent(interval=0.1),
    }

    memory = psutil.virtual_memory()
    memory_info = {
        "total_gb": round(memory.total / 1024**3, 1),
        "available_gb": round(memory.available / 1024**3, 1),
        "used_percent": memory.percent,
    }

    disk = psutil.disk_usage(str(get_settings().storage.outputs_dir))
    disk_info = {
        "total_gb": round(disk.total / 1024**3, 1),
        "free_gb": round(disk.free / 1024**3, 1),
        "used_percent": round(disk.percent, 1),
    }

    return {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "cpu": cpu_info,
        "memory": memory_info,
        "disk": disk_info,
        "gpu": get_gpu_info(),
    }
