"""Event broadcasting for real-time ingestion updates."""

from __future__ import annotations

import asyncio
from typing import Any

# Global event queue for broadcasting ingestion progress
_event_subscribers: set[asyncio.Queue] = set()


async def subscribe() -> asyncio.Queue:
    """Subscribe to ingestion events."""
    queue: asyncio.Queue = asyncio.Queue()
    _event_subscribers.add(queue)
    return queue


def unsubscribe(queue: asyncio.Queue) -> None:
    """Unsubscribe from ingestion events."""
    _event_subscribers.discard(queue)


async def broadcast_event(event: dict[str, Any]) -> None:
    """Broadcast an event to all subscribers."""
    dead_queues = []
    for queue in _event_subscribers:
        try:
            queue.put_nowait(event)
        except asyncio.QueueFull:
            dead_queues.append(queue)

    # Clean up dead queues
    for queue in dead_queues:
        _event_subscribers.discard(queue)
