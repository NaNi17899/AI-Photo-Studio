"""
Preset management API endpoints.
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from backend.database import get_session, Preset

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/presets", tags=["presets"])


class PresetCreate(BaseModel):
    name: str
    plugin: str
    category: str = "custom"
    description: str = ""
    params: dict


class PresetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    params: Optional[dict] = None


@router.get("")
async def list_presets(plugin: Optional[str] = None, category: Optional[str] = None):
    """List presets, optionally filtered by plugin or category."""
    session = get_session()
    try:
        query = session.query(Preset)
        if plugin:
            query = query.filter(Preset.plugin == plugin)
        if category:
            query = query.filter(Preset.category == category)
        presets = query.order_by(Preset.is_builtin.desc(), Preset.name).all()
        return {
            "presets": [
                {
                    "id": p.id,
                    "name": p.name,
                    "plugin": p.plugin,
                    "category": p.category,
                    "description": p.description,
                    "params": p.params,
                    "is_builtin": p.is_builtin,
                }
                for p in presets
            ]
        }
    finally:
        session.close()


@router.post("")
async def create_preset(data: PresetCreate):
    """Create a new custom preset."""
    session = get_session()
    try:
        preset = Preset(
            name=data.name,
            plugin=data.plugin,
            category=data.category,
            description=data.description,
            params=data.params,
            is_builtin=False,
        )
        session.add(preset)
        session.commit()
        return {"id": preset.id, "message": "Preset created"}
    except Exception as e:
        session.rollback()
        raise HTTPException(500, str(e))
    finally:
        session.close()


@router.put("/{preset_id}")
async def update_preset(preset_id: int, data: PresetUpdate):
    """Update a custom preset."""
    session = get_session()
    try:
        preset = session.query(Preset).filter(Preset.id == preset_id).first()
        if not preset:
            raise HTTPException(404, "Preset not found")
        if preset.is_builtin:
            raise HTTPException(403, "Cannot modify built-in presets")

        if data.name is not None:
            preset.name = data.name
        if data.description is not None:
            preset.description = data.description
        if data.params is not None:
            preset.params = data.params

        session.commit()
        return {"message": "Preset updated"}
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(500, str(e))
    finally:
        session.close()


@router.delete("/{preset_id}")
async def delete_preset(preset_id: int):
    """Delete a custom preset."""
    session = get_session()
    try:
        preset = session.query(Preset).filter(Preset.id == preset_id).first()
        if not preset:
            raise HTTPException(404, "Preset not found")
        if preset.is_builtin:
            raise HTTPException(403, "Cannot delete built-in presets")

        session.delete(preset)
        session.commit()
        return {"message": "Preset deleted"}
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(500, str(e))
    finally:
        session.close()
