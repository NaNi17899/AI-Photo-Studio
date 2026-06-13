"""
File upload API endpoints.
"""

import os
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from typing import List

from backend.storage.file_manager import get_file_manager
from backend.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/upload", tags=["upload"])


@router.post("")
async def upload_file(file: UploadFile = File(...)):
    """Upload a single image file."""
    settings = get_settings()
    max_size = settings.storage.max_upload_size_mb * 1024 * 1024

    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(400, f"File too large. Max: {settings.storage.max_upload_size_mb} MB")

    try:
        fm = get_file_manager()
        result = fm.save_upload(file.filename, content)
        return result
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error("Upload failed: %s", e)
        raise HTTPException(500, "Upload failed")


@router.post("/batch")
async def upload_batch(files: List[UploadFile] = File(...)):
    """Upload multiple image files."""
    results = []
    fm = get_file_manager()
    settings = get_settings()
    max_size = settings.storage.max_upload_size_mb * 1024 * 1024

    for file in files:
        content = await file.read()
        if len(content) > max_size:
            results.append({"filename": file.filename, "error": "File too large"})
            continue
        try:
            result = fm.save_upload(file.filename, content)
            results.append(result)
        except Exception as e:
            results.append({"filename": file.filename, "error": str(e)})

    return {
        "uploaded": len([r for r in results if "error" not in r]),
        "failed": len([r for r in results if "error" in r]),
        "results": results,
    }


@router.get("/file/{file_id}")
async def get_uploaded_file(file_id: str):
    """Serve an uploaded file by ID."""
    fm = get_file_manager()
    path = fm.get_upload_path(file_id)
    if not path or not os.path.exists(path):
        raise HTTPException(404, "File not found")
    return FileResponse(path)


@router.get("/thumb/{file_id}")
async def get_thumbnail(file_id: str):
    """Serve a thumbnail for an uploaded file."""
    settings = get_settings()
    thumb_path = settings.storage.uploads_dir / "thumbs" / f"{file_id}_thumb.webp"
    if not thumb_path.exists():
        raise HTTPException(404, "Thumbnail not found")
    return FileResponse(str(thumb_path))


@router.get("/backgrounds")
async def list_backgrounds():
    """List available background images."""
    fm = get_file_manager()
    return fm.list_backgrounds()
