"""
WebSocket endpoint for real-time job progress updates.
"""

import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.core.job_queue import get_job_queue

logger = logging.getLogger(__name__)
router = APIRouter(tags=["websocket"])


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    """
    WebSocket endpoint for real-time progress updates.

    Clients connect here and receive JSON messages:
    {
        "type": "job_progress",
        "job": { ...job data... }
    }
    """
    await ws.accept()
    queue = get_job_queue()
    queue.register_ws_client(ws)
    logger.info("WebSocket client connected")

    try:
        # Send current active jobs on connect
        active = queue.get_active_jobs()
        if active:
            await ws.send_json(
                {
                    "type": "initial_state",
                    "active_jobs": [j.to_dict() for j in active],
                }
            )

        # Keep connection alive — listen for pings
        while True:
            data = await ws.receive_text()
            if data == "ping":
                await ws.send_json({"type": "pong"})
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.warning("WebSocket error: %s", e)
    finally:
        queue.unregister_ws_client(ws)
