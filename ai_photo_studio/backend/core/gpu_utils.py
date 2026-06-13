"""
GPU and CUDA utility functions.
Handles device detection, VRAM monitoring, mixed precision, and CPU fallback.
"""

import gc
import logging
import functools
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Lazy torch import to avoid startup cost if not needed
_torch = None


def _get_torch():
    """Lazy import torch. Returns None if torch is not installed."""
    global _torch
    if _torch is None:
        try:
            import torch

            _torch = torch
        except ImportError:
            logger.warning("PyTorch not installed — GPU features unavailable")
            return None
    return _torch


def get_device(preferred: str = "auto") -> str:
    """
    Determine the best available device.

    Args:
        preferred: 'cuda', 'cpu', or 'auto'

    Returns:
        Device string ('cuda' or 'cpu')
    """
    torch = _get_torch()
    if torch is None or preferred == "cpu":
        return "cpu"
    if preferred == "cuda" or preferred == "auto":
        if torch.cuda.is_available():
            return "cuda"
        else:
            logger.warning("CUDA not available, falling back to CPU")
            return "cpu"
    return "cpu"


def get_gpu_info() -> dict:
    """Get GPU information including VRAM stats."""
    torch = _get_torch()
    info = {
        "cuda_available": torch.cuda.is_available() if torch else False,
        "device_count": 0,
        "devices": [],
        "current_device": None,
    }
    if torch and torch.cuda.is_available():
        info["device_count"] = torch.cuda.device_count()
        for i in range(torch.cuda.device_count()):
            props = torch.cuda.get_device_properties(i)
            mem_allocated = torch.cuda.memory_allocated(i) / 1024**2
            mem_reserved = torch.cuda.memory_reserved(i) / 1024**2
            mem_total = props.total_memory / 1024**2
            info["devices"].append(
                {
                    "index": i,
                    "name": props.name,
                    "total_vram_mb": round(mem_total, 1),
                    "allocated_mb": round(mem_allocated, 1),
                    "reserved_mb": round(mem_reserved, 1),
                    "free_mb": round(mem_total - mem_allocated, 1),
                    "compute_capability": f"{props.major}.{props.minor}",
                }
            )
        info["current_device"] = torch.cuda.current_device()
    return info


def get_vram_free_mb() -> float:
    """Get free VRAM in MB. Returns 0 if CUDA unavailable."""
    torch = _get_torch()
    if not torch or not torch.cuda.is_available():
        return 0.0
    props = torch.cuda.get_device_properties(0)
    allocated = torch.cuda.memory_allocated(0)
    total = props.total_memory
    return (total - allocated) / 1024**2


def get_vram_used_mb() -> float:
    """Get used VRAM in MB."""
    torch = _get_torch()
    if not torch or not torch.cuda.is_available():
        return 0.0
    return torch.cuda.memory_allocated(0) / 1024**2


def get_vram_total_mb() -> float:
    """Get total VRAM in MB."""
    torch = _get_torch()
    if not torch or not torch.cuda.is_available():
        return 0.0
    return torch.cuda.get_device_properties(0).total_memory / 1024**2


def clear_vram():
    """Aggressively clear VRAM — garbage collect and empty cache."""
    torch = _get_torch()
    gc.collect()
    if torch and torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()
    logger.info(f"VRAM cleared. Free: {get_vram_free_mb():.0f} MB")


@contextmanager
def mixed_precision_context(enabled: bool = True):
    """Context manager for automatic mixed precision (fp16)."""
    torch = _get_torch()
    if enabled and torch and torch.cuda.is_available():
        with torch.cuda.amp.autocast():
            yield
    else:
        yield


def cpu_fallback(func):
    """
    Decorator that automatically falls back to CPU if GPU processing fails.
    Catches CUDA OOM errors and retries on CPU.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        torch = _get_torch()
        if torch is None:
            return func(*args, **kwargs)
        try:
            return func(*args, **kwargs)
        except (torch.cuda.OutOfMemoryError, RuntimeError) as e:
            if "out of memory" in str(e).lower() or "CUDA" in str(e):
                logger.warning(f"GPU OOM in {func.__name__}, retrying on CPU...")
                clear_vram()
                # Set a flag for the function to detect
                kwargs["_force_cpu"] = True
                return func(*args, **kwargs)
            raise

    return wrapper


def optimal_dtype(prefer_half: bool = True) -> "torch.dtype":
    """Get the optimal dtype for the current GPU."""
    torch = _get_torch()
    if torch is None:
        return None
    if prefer_half and torch.cuda.is_available():
        # GTX 1650 supports fp16
        return torch.float16
    return torch.float32


def estimate_image_vram_mb(
    width: int,
    height: int,
    channels: int = 3,
    dtype_bytes: int = 2,
    batch_size: int = 1,
    overhead_factor: float = 3.0,
) -> float:
    """
    Estimate VRAM required for an image tensor including model overhead.

    Args:
        overhead_factor: Multiplier for intermediate tensors during processing
    """
    tensor_size = width * height * channels * dtype_bytes * batch_size
    return (tensor_size * overhead_factor) / 1024**2


def should_use_tiles(width: int, height: int, max_pixels: int = 1024 * 1024) -> bool:
    """Check if an image should be processed in tiles to avoid OOM."""
    return (width * height) > max_pixels
