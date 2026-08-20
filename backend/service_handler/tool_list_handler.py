from __future__ import annotations

import json

from fastapi.responses import StreamingResponse

from utils.tool_events import register_queue, unregister_queue


async def handle_tool_events(chat_id: str):
    queue = register_queue(chat_id)

    try:
        async def event_generator():
            try:
                while True:
                    event = await queue.get()
                    yield f"event: {event['type']}\ndata: {json.dumps(event)}\n\n"
            finally:
                unregister_queue(chat_id, queue)

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    except Exception:
        unregister_queue(chat_id, queue)
        raise
