"""WebSocket endpoint for real-time ingestion progress."""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.app.core.events import subscribe, unsubscribe

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/ingest/progress")
async def ingest_progress_websocket(websocket: WebSocket) -> None:
    """Stream real-time ingestion progress events."""
    await websocket.accept()
    queue = await subscribe()

    try:
        # Send initial connection confirmation
        await websocket.send_json({"type": "connected"})

        while True:
            try:
                # Wait for event with timeout to allow periodic checks
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                await websocket.send_json(event)
            except asyncio.TimeoutError:
                # Send heartbeat to keep connection alive
                await websocket.send_json({"type": "heartbeat"})
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        unsubscribe(queue)
        try:
            await websocket.close()
        except Exception:
            pass
