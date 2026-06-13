"""
VRAM-aware Model Manager.
Handles loading, unloading, and LRU eviction of AI models
to stay within the GTX 1650's 4GB VRAM budget.
"""

import time
import asyncio
import logging
import threading
from enum import Enum
from typing import Any, Callable, Optional
from dataclasses import dataclass

from backend.core.gpu_utils import get_vram_free_mb, clear_vram

logger = logging.getLogger(__name__)


class ModelState(str, Enum):
    UNLOADED = "unloaded"
    LOADING = "loading"
    READY = "ready"
    PROCESSING = "processing"
    ERROR = "error"


@dataclass
class ModelEntry:
    """Tracks a loaded model's state and metadata."""

    name: str
    model: Any = None
    state: ModelState = ModelState.UNLOADED
    vram_mb: int = 0  # Estimated VRAM usage
    last_used: float = 0.0
    load_fn: Optional[Callable] = None  # Function to load the model
    unload_fn: Optional[Callable] = None  # Function to unload (optional custom)
    error: Optional[str] = None
    load_count: int = 0  # Times this model has been loaded


class ModelManager:
    """
    Singleton model manager with VRAM-aware loading.

    Key behaviors:
    - Tracks all registered models and their VRAM requirements
    - LRU eviction when VRAM is insufficient for a new model
    - Idle timeout auto-unload
    - Thread-safe model access
    - Exclusive mode for large models (e.g., Stable Diffusion)
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._models: dict[str, ModelEntry] = {}
        self._async_lock = asyncio.Lock()
        self._max_vram_mb: int = 3500  # Safe limit for GTX 1650
        self._idle_timeout_seconds: int = 300
        self._idle_timer_task: Optional[asyncio.Task] = None
        logger.info("ModelManager initialized (max VRAM: %d MB)", self._max_vram_mb)

    def configure(self, max_vram_mb: int = 3500, idle_timeout: int = 300):
        """Update manager configuration."""
        self._max_vram_mb = max_vram_mb
        self._idle_timeout_seconds = idle_timeout

    def register(
        self, name: str, load_fn: Callable, vram_mb: int, unload_fn: Optional[Callable] = None
    ):
        """
        Register a model with its loader function and VRAM requirement.

        Args:
            name: Unique model identifier
            load_fn: Callable that returns the loaded model object
            vram_mb: Estimated VRAM usage in MB
            unload_fn: Optional custom unload function
        """
        self._models[name] = ModelEntry(
            name=name,
            load_fn=load_fn,
            vram_mb=vram_mb,
            unload_fn=unload_fn,
        )
        logger.debug("Registered model '%s' (VRAM: %d MB)", name, vram_mb)

    async def load(self, name: str) -> Any:
        """
        Load a model, evicting others if needed to fit in VRAM.
        Returns the loaded model object.
        """
        async with self._async_lock:
            if name not in self._models:
                raise KeyError(f"Model '{name}' not registered")

            entry = self._models[name]

            # Already loaded — just update timestamp
            if entry.state == ModelState.READY and entry.model is not None:
                entry.last_used = time.time()
                return entry.model

            # Already loading — wait (shouldn't happen with async lock, but safety)
            if entry.state == ModelState.LOADING:
                logger.warning("Model '%s' already loading, waiting...", name)
                while entry.state == ModelState.LOADING:
                    await asyncio.sleep(0.1)
                return entry.model

            # Need to load — check VRAM budget
            required_mb = entry.vram_mb
            await self._ensure_vram(required_mb, exclude=name)

            # Load the model
            entry.state = ModelState.LOADING
            entry.error = None
            try:
                logger.info("Loading model '%s' (est. %d MB VRAM)...", name, required_mb)
                # Run the load function in a thread to avoid blocking
                loop = asyncio.get_event_loop()
                model = await loop.run_in_executor(None, entry.load_fn)
                entry.model = model
                entry.state = ModelState.READY
                entry.last_used = time.time()
                entry.load_count += 1
                logger.info("Model '%s' loaded successfully", name)
                return model
            except Exception as e:
                entry.state = ModelState.ERROR
                entry.error = str(e)
                logger.error("Failed to load model '%s': %s", name, e)
                raise

    def load_sync(self, name: str) -> Any:
        """Synchronous model loading for non-async contexts."""
        if name not in self._models:
            raise KeyError(f"Model '{name}' not registered")

        entry = self._models[name]

        if entry.state == ModelState.READY and entry.model is not None:
            entry.last_used = time.time()
            return entry.model

        # Evict if needed (synchronous version)
        self._ensure_vram_sync(entry.vram_mb, exclude=name)

        entry.state = ModelState.LOADING
        try:
            model = entry.load_fn()
            entry.model = model
            entry.state = ModelState.READY
            entry.last_used = time.time()
            entry.load_count += 1
            return model
        except Exception as e:
            entry.state = ModelState.ERROR
            entry.error = str(e)
            raise

    async def unload(self, name: str):
        """Unload a specific model and free its VRAM."""
        async with self._async_lock:
            self._unload_internal(name)

    def unload_sync(self, name: str):
        """Synchronous unload."""
        self._unload_internal(name)

    def _unload_internal(self, name: str):
        """Internal unload without locking."""
        if name not in self._models:
            return

        entry = self._models[name]
        if entry.state == ModelState.UNLOADED:
            return

        logger.info("Unloading model '%s'...", name)

        if entry.unload_fn:
            try:
                entry.unload_fn(entry.model)
            except Exception as e:
                logger.warning("Custom unload for '%s' failed: %s", name, e)

        # Delete the model reference
        entry.model = None
        entry.state = ModelState.UNLOADED
        clear_vram()
        logger.info("Model '%s' unloaded. Free VRAM: %.0f MB", name, get_vram_free_mb())

    async def unload_all(self):
        """Emergency: unload all models."""
        async with self._async_lock:
            for name in list(self._models.keys()):
                self._unload_internal(name)
            clear_vram()
            logger.info("All models unloaded")

    def unload_all_sync(self):
        """Synchronous unload all."""
        for name in list(self._models.keys()):
            self._unload_internal(name)
        clear_vram()

    async def _ensure_vram(self, required_mb: int, exclude: str = ""):
        """Evict LRU models until we have enough free VRAM."""
        free = get_vram_free_mb()
        if free >= required_mb:
            return

        # Get loaded models sorted by last_used (oldest first)
        loaded = sorted(
            [e for e in self._models.values() if e.state == ModelState.READY and e.name != exclude],
            key=lambda e: e.last_used,
        )

        for entry in loaded:
            if free >= required_mb:
                break
            logger.info("Evicting model '%s' (LRU) to free VRAM", entry.name)
            self._unload_internal(entry.name)
            free = get_vram_free_mb()

        # Final check
        if get_vram_free_mb() < required_mb:
            logger.warning(
                "VRAM still insufficient after eviction (need %d MB, have %.0f MB). "
                "Processing may fall back to CPU.",
                required_mb,
                get_vram_free_mb(),
            )

    def _ensure_vram_sync(self, required_mb: int, exclude: str = ""):
        """Synchronous VRAM eviction."""
        free = get_vram_free_mb()
        if free >= required_mb:
            return

        loaded = sorted(
            [e for e in self._models.values() if e.state == ModelState.READY and e.name != exclude],
            key=lambda e: e.last_used,
        )

        for entry in loaded:
            if get_vram_free_mb() >= required_mb:
                break
            self._unload_internal(entry.name)

    def get_status(self) -> dict:
        """Get status of all registered models."""
        return {
            name: {
                "state": entry.state.value,
                "vram_mb": entry.vram_mb,
                "last_used": entry.last_used,
                "load_count": entry.load_count,
                "error": entry.error,
            }
            for name, entry in self._models.items()
        }

    def get_loaded_models(self) -> list[str]:
        """Get names of currently loaded models."""
        return [name for name, entry in self._models.items() if entry.state == ModelState.READY]

    def get_total_vram_used_by_models(self) -> int:
        """Estimated total VRAM used by loaded models."""
        return sum(
            entry.vram_mb for entry in self._models.values() if entry.state == ModelState.READY
        )

    async def start_idle_monitor(self):
        """Start background task to unload idle models."""

        async def _monitor():
            while True:
                await asyncio.sleep(60)  # Check every minute
                now = time.time()
                async with self._async_lock:
                    for entry in self._models.values():
                        if (
                            entry.state == ModelState.READY
                            and entry.last_used > 0
                            and (now - entry.last_used) > self._idle_timeout_seconds
                        ):
                            logger.info(
                                "Auto-unloading idle model '%s' (idle %.0f s)",
                                entry.name,
                                now - entry.last_used,
                            )
                            self._unload_internal(entry.name)

        self._idle_timer_task = asyncio.create_task(_monitor())

    async def stop_idle_monitor(self):
        """Stop the idle monitor task."""
        if self._idle_timer_task:
            self._idle_timer_task.cancel()
            try:
                await self._idle_timer_task
            except asyncio.CancelledError:
                pass


# Module-level convenience function
def get_model_manager() -> ModelManager:
    """Get the global ModelManager singleton."""
    return ModelManager()
