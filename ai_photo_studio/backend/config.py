"""
Application configuration using Pydantic Settings.
All settings can be overridden via environment variables or .env file.
"""

from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
DATA_DIR = PROJECT_ROOT / "data"


class GPUSettings(BaseSettings):
    """GPU and CUDA configuration."""

    device: str = Field(default="auto", description="Device: 'cuda', 'cpu', or 'auto'")
    max_vram_usage_mb: int = Field(
        default=3500, description="Max VRAM usage in MB (safe for GTX 1650)"
    )
    mixed_precision: bool = Field(default=True, description="Use fp16 where possible")
    tile_size: int = Field(default=256, description="Tile size for tiled processing")
    tile_pad: int = Field(default=10, description="Tile padding overlap")
    idle_unload_seconds: int = Field(default=300, description="Unload models after N seconds idle")

    class Config:
        env_prefix = "GPU_"


class StorageSettings(BaseSettings):
    """File storage paths."""

    models_dir: Path = Field(default=DATA_DIR / "models")
    uploads_dir: Path = Field(default=DATA_DIR / "uploads")
    outputs_dir: Path = Field(default=DATA_DIR / "outputs")
    luts_dir: Path = Field(default=DATA_DIR / "luts")
    backgrounds_dir: Path = Field(default=DATA_DIR / "backgrounds")
    db_dir: Path = Field(default=DATA_DIR / "db")
    loras_dir: Path = Field(default=DATA_DIR / "models" / "loras")
    max_upload_size_mb: int = Field(default=50, description="Max upload file size in MB")
    max_output_retention_days: int = Field(
        default=30, description="Auto-delete outputs older than N days"
    )

    class Config:
        env_prefix = "STORAGE_"

    def ensure_dirs(self):
        """Create all storage directories."""
        for field_name in self.model_fields:
            val = getattr(self, field_name)
            if isinstance(val, Path):
                val.mkdir(parents=True, exist_ok=True)


class ServerSettings(BaseSettings):
    """Server configuration."""

    host: str = Field(default="127.0.0.1")
    port: int = Field(default=8000)
    workers: int = Field(default=1, description="Uvicorn workers (keep 1 for GPU)")
    cors_origins: list[str] = Field(
        default=["http://localhost:5173", "http://localhost:8000", "http://127.0.0.1:5173"]
    )
    log_level: str = Field(default="INFO")
    debug: bool = Field(default=False)

    class Config:
        env_prefix = "SERVER_"


class ModelRegistryEntry:
    """Metadata for a downloadable model."""

    def __init__(
        self,
        name: str,
        filename: str,
        url: str,
        size_mb: float,
        vram_mb: int,
        description: str,
        required: bool = False,
        checksum: Optional[str] = None,
    ):
        self.name = name
        self.filename = filename
        self.url = url
        self.size_mb = size_mb
        self.vram_mb = vram_mb
        self.description = description
        self.required = required
        self.checksum = checksum


# Central model registry — all downloadable models
MODEL_REGISTRY: dict[str, ModelRegistryEntry] = {
    "gfpgan_v1.4": ModelRegistryEntry(
        name="gfpgan_v1.4",
        filename="GFPGANv1.4.pth",
        url="https://github.com/TencentARC/GFPGAN/releases/download/v1.3.4/GFPGANv1.4.pth",
        size_mb=332,
        vram_mb=500,
        description="GFPGAN v1.4 face restoration",
        required=True,
    ),
    "realesrgan_x4plus": ModelRegistryEntry(
        name="realesrgan_x4plus",
        filename="RealESRGAN_x4plus.pth",
        url="https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth",
        size_mb=64,
        vram_mb=400,
        description="Real-ESRGAN 4x general upscaler",
        required=True,
    ),
    "realesrgan_x4_anime": ModelRegistryEntry(
        name="realesrgan_x4_anime",
        filename="RealESRGAN_x4plus_anime_6B.pth",
        url="https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth",
        size_mb=64,
        vram_mb=300,
        description="Real-ESRGAN 4x anime upscaler",
    ),
    "realesrgan_x2plus": ModelRegistryEntry(
        name="realesrgan_x2plus",
        filename="RealESRGAN_x2plus.pth",
        url="https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth",
        size_mb=64,
        vram_mb=300,
        description="Real-ESRGAN 2x general upscaler",
    ),
    "codeformer": ModelRegistryEntry(
        name="codeformer",
        filename="codeformer.pth",
        url="https://github.com/sczhou/CodeFormer/releases/download/v0.1.0/codeformer.pth",
        size_mb=376,
        vram_mb=500,
        description="CodeFormer face restoration",
    ),
    "detection_Resnet50": ModelRegistryEntry(
        name="detection_Resnet50",
        filename="detection_Resnet50_Final.pth",
        url="https://github.com/sczhou/CodeFormer/releases/download/v0.1.0/detection_Resnet50_Final.pth",
        size_mb=109,
        vram_mb=100,
        description="Face detection model for CodeFormer",
    ),
    "parsing_parsenet": ModelRegistryEntry(
        name="parsing_parsenet",
        filename="parsing_parsenet.pth",
        url="https://github.com/sczhou/CodeFormer/releases/download/v0.1.0/parsing_parsenet.pth",
        size_mb=81,
        vram_mb=100,
        description="Face parsing model for CodeFormer",
    ),
}


class AppSettings(BaseSettings):
    """Root application settings."""

    app_name: str = "AI Photo Studio"
    version: str = "2.0.0"
    gpu: GPUSettings = GPUSettings()
    storage: StorageSettings = StorageSettings()
    server: ServerSettings = ServerSettings()

    class Config:
        env_file = str(PROJECT_ROOT / ".env")
        env_file_encoding = "utf-8"


# Global singleton
_settings: Optional[AppSettings] = None


def get_settings() -> AppSettings:
    """Get or create the global settings instance."""
    global _settings
    if _settings is None:
        _settings = AppSettings()
        _settings.storage.ensure_dirs()
    return _settings
