"""
AI Photo Studio — FastAPI Application Entry Point.

Initializes database, model manager, plugin registry, job queue,
and mounts all API routers with CORS and static file serving.
"""

import os
import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Ensure the project root is in sys.path
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import get_settings  # noqa: E402
from backend.database import init_db  # noqa: E402
from backend.core.job_queue import get_job_queue  # noqa: E402
from backend.core.model_manager import get_model_manager  # noqa: E402
from backend.core.plugin_registry import discover_and_register_plugins  # noqa: E402

# Import API routers
from backend.api.upload import router as upload_router  # noqa: E402
from backend.api.jobs import router as jobs_router  # noqa: E402
from backend.api.ws import router as ws_router  # noqa: E402
from backend.api.presets import router as presets_router  # noqa: E402
from backend.api.models_api import router as models_router  # noqa: E402
from backend.api.settings_api import router as settings_router  # noqa: E402

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(str(PROJECT_ROOT / "data" / "photo_studio.log"), encoding="utf-8"),
    ],
)
logger = logging.getLogger("ai_photo_studio")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    settings = get_settings()
    logger.info("=" * 60)
    logger.info("  AI Photo Studio v%s starting up...", settings.version)
    logger.info("=" * 60)

    # Initialize database
    init_db()
    logger.info("Database initialized")

    # Configure model manager
    mm = get_model_manager()
    mm.configure(
        max_vram_mb=settings.gpu.max_vram_usage_mb,
        idle_timeout=settings.gpu.idle_unload_seconds,
    )

    # Discover and register plugins
    try:
        discover_and_register_plugins()
    except Exception as e:
        logger.error("Plugin registration failed: %s", e)
        logger.info("Some features may be unavailable")

    # Start job queue
    queue = get_job_queue()
    await queue.start()
    logger.info("Job queue started")

    # Start idle model monitor
    await mm.start_idle_monitor()
    logger.info("Idle model monitor started")

    logger.info("=" * 60)
    logger.info("  Server ready at http://%s:%d", settings.server.host, settings.server.port)
    logger.info("  Frontend at http://localhost:5173")
    logger.info("=" * 60)

    yield  # Application is running

    # Shutdown
    logger.info("Shutting down...")
    await queue.stop()
    await mm.stop_idle_monitor()
    mm.unload_all_sync()
    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="AI Photo Studio",
    version="2.0.0",
    description="Professional AI photo editing platform",
    lifespan=lifespan,
)

# CORS middleware
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.server.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(upload_router)
app.include_router(jobs_router)
app.include_router(ws_router)
app.include_router(presets_router)
app.include_router(models_router)
app.include_router(settings_router)


# Serve output files
outputs_dir = str(get_settings().storage.outputs_dir)
os.makedirs(outputs_dir, exist_ok=True)
app.mount("/outputs", StaticFiles(directory=outputs_dir), name="outputs")

# Serve upload files
uploads_dir = str(get_settings().storage.uploads_dir)
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

# Serve frontend build (production)
frontend_build = PROJECT_ROOT / "frontend" / "dist"
if frontend_build.exists():
    app.mount(
        "/assets", StaticFiles(directory=str(frontend_build / "assets")), name="frontend_assets"
    )

    @app.get("/")
    async def serve_frontend():
        return FileResponse(str(frontend_build / "index.html"))

    @app.get("/{path:path}")
    async def serve_frontend_routes(path: str):
        """Catch-all for SPA routes."""
        file_path = frontend_build / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(frontend_build / "index.html"))
else:

    @app.get("/")
    async def root():
        return {
            "app": "AI Photo Studio",
            "version": "2.0.0",
            "status": "running",
            "api_docs": "/docs",
            "note": "Frontend not built. Run 'npm run build' in frontend/ directory, or access dev server at http://localhost:5173",
        }


# API info endpoint
@app.get("/api/info")
async def api_info():
    """Basic API information."""
    from backend.core.plugin_registry import get_plugin_registry

    registry = get_plugin_registry()
    return {
        "app": "AI Photo Studio",
        "version": "2.0.0",
        "plugins": registry.get_info_all(),
    }


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "backend.main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=settings.server.debug,
        log_level=settings.server.log_level.lower(),
    )
