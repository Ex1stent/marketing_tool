from __future__ import annotations
import asyncio
import json
from typing import Dict, Set

# Global registry: chat_id -> set of queues
_active_queues: Dict[str, Set[asyncio.Queue]] = {}


async def broadcast_tool_event(chat_id: str, event: dict):
    """Send event to all registered queues for a chat."""
    if chat_id in _active_queues:
        for queue in list(_active_queues[chat_id]):
            await queue.put(event)


def register_queue(chat_id: str) -> asyncio.Queue:
    """Register a new queue for a chat and return it."""
    queue: asyncio.Queue = asyncio.Queue()
    if chat_id not in _active_queues:
        _active_queues[chat_id] = set()
    _active_queues[chat_id].add(queue)
    return queue


def unregister_queue(chat_id: str, queue: asyncio.Queue):
    """Unregister a queue from a chat."""
    if chat_id in _active_queues:
        _active_queues[chat_id].discard(queue)
        if not _active_queues[chat_id]:
            del _active_queues[chat_id]
