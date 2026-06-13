"""
File storage manager — handles uploads, outputs, thumbnails, and cleanup.
"""

import os
import uuid
import logging
from pathlib import Path
from typing import Optional
from PIL import Image

from backend.config import get_settings

logger = logging.getLogger(__name__)


class FileManager:
    """Manages file uploads, outputs, and storage cleanup."""

    def __init__(self):
        self.settings = get_settings().storage

    def save_upload(self, filename: str, content: bytes) -> dict:
        """
        Save an uploaded file and create a thumbnail.

        Returns:
            dict with file_id, path, thumbnail_path, and info
        """
        file_id = str(uuid.uuid4())[:8]
        ext = os.path.splitext(filename)[1].lower()
        if ext not in (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"):
            raise ValueError(f"Unsupported file type: {ext}")

        # Save original
        safe_name = f"{file_id}{ext}"
        path = self.settings.uploads_dir / safe_name
        path.write_bytes(content)

        # Create thumbnail
        thumb_dir = self.settings.uploads_dir / "thumbs"
        thumb_dir.mkdir(exist_ok=True)
        thumb_path = thumb_dir / f"{file_id}_thumb.webp"
        try:
            img = Image.open(path)
            img.thumbnail((256, 256), Image.LANCZOS)
            img.save(thumb_path, "WEBP", quality=80)
        except Exception as e:
            logger.warning("Failed to create thumbnail for %s: %s", filename, e)
            thumb_path = None

        # Get image info
        img = Image.open(path)
        info = {
            "file_id": file_id,
            "original_name": filename,
            "path": str(path),
            "thumbnail_path": str(thumb_path) if thumb_path else None,
            "width": img.size[0],
            "height": img.size[1],
            "format": img.format,
            "size_bytes": os.path.getsize(path),
        }

        logger.info("Saved upload: %s -> %s", filename, path)
        return info

    def get_upload_path(self, file_id: str) -> Optional[str]:
        """Get the full path for an uploaded file by its ID."""
        for ext in (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"):
            path = self.settings.uploads_dir / f"{file_id}{ext}"
            if path.exists():
                return str(path)
        return None

    def get_output_path(self, filename: str) -> str:
        """Get the full path for an output file."""
        return str(self.settings.outputs_dir / filename)

    def list_outputs(self, limit: int = 50, offset: int = 0) -> list[dict]:
        """List output files with metadata."""
        outputs = []
        output_dir = self.settings.outputs_dir
        if not output_dir.exists():
            return []

        files = sorted(output_dir.glob("*.*"), key=lambda f: f.stat().st_mtime, reverse=True)
        for f in files[offset : offset + limit]:
            if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
                outputs.append(
                    {
                        "filename": f.name,
                        "path": str(f),
                        "size_bytes": f.stat().st_size,
                        "modified_at": f.stat().st_mtime,
                    }
                )
        return outputs

    def list_backgrounds(self) -> list[dict]:
        """List available background images."""
        bg_dir = self.settings.backgrounds_dir
        if not bg_dir.exists():
            return []

        backgrounds = []
        for f in bg_dir.glob("*.*"):
            if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
                backgrounds.append(
                    {
                        "filename": f.name,
                        "path": str(f),
                    }
                )
        return backgrounds

    def get_disk_usage(self) -> dict:
        """Get disk usage statistics for storage directories."""

        def dir_size(path: Path) -> int:
            if not path.exists():
                return 0
            return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())

        return {
            "uploads_mb": round(dir_size(self.settings.uploads_dir) / 1024**2, 1),
            "outputs_mb": round(dir_size(self.settings.outputs_dir) / 1024**2, 1),
            "models_mb": round(dir_size(self.settings.models_dir) / 1024**2, 1),
            "total_mb": round(
                (
                    dir_size(self.settings.uploads_dir)
                    + dir_size(self.settings.outputs_dir)
                    + dir_size(self.settings.models_dir)
                )
                / 1024**2,
                1,
            ),
        }

    def cleanup_old_outputs(self, max_age_days: int = 30):
        """Delete output files older than max_age_days."""
        import time

        cutoff = time.time() - (max_age_days * 86400)
        output_dir = self.settings.outputs_dir
        if not output_dir.exists():
            return 0

        deleted = 0
        for f in output_dir.glob("*.*"):
            if f.stat().st_mtime < cutoff:
                f.unlink()
                deleted += 1

        if deleted > 0:
            logger.info("Cleaned up %d old output files", deleted)
        return deleted


_file_manager: Optional[FileManager] = None


def get_file_manager() -> FileManager:
    """Get the global FileManager singleton."""
    global _file_manager
    if _file_manager is None:
        _file_manager = FileManager()
    return _file_manager
