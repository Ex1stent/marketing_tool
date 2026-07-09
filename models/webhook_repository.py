from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from models.database import Base, SessionLocal

WebhookEvent = Base.classes.webhook_events


def _to_timestamp(value: Any):
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    try:
        raw_value = int(value)
        if raw_value > 10_000_000_000:
            raw_value = raw_value / 1000
        return datetime.fromtimestamp(raw_value, tz=timezone.utc).replace(tzinfo=None)
    except (TypeError, ValueError, OSError):
        return value


class WebhookRepository:
    def get_session(self):
        return SessionLocal()

    def save_event(self, session, event: dict[str, Any]):
        row = WebhookEvent(
            chatsession_id=event.get("chatsession_id") or 0,
            platform=event.get("platform"),
            direction="inbound",
            sender_id=event.get("sender_id"),
            recipient_id=event.get("recipient_id") or "",
            sender_type=event.get("sender_type") or ("contact" if event.get("platform") == "whatsapp" else "user"),
            message_id=event.get("message_id"),
            message_type=event.get("message_type") or event.get("event_type") or "text",
            message_text=event.get("text"),
            status=event.get("status") or "received",
            is_echo=bool(event.get("is_echo", False)),
            media_id=event.get("media_id"),
            media_url=event.get("media_url"),
            mime_type=event.get("mime_type"),
            file_name=event.get("file_name"),
            caption=event.get("caption"),
            webhook_timestamp=_to_timestamp(event.get("timestamp")),
            message_json=event.get("message_json") or event,
        )
        session.add(row)
        session.flush()
        return row

    def save_reply(self, session, sender_id: str | None, reply: dict[str, Any], event: dict[str, Any]):
        row = WebhookEvent(
            chatsession_id=event.get("chatsession_id") or 0,
            platform=event.get("platform"),
            direction="outbound",
            sender_id=sender_id or event.get("recipient_id") or "",
            recipient_id=event.get("sender_id") or event.get("recipient_id") or "",
            sender_type="business",
            message_id=None,
            message_type="text",
            message_text=reply.get("reply_text"),
            status=reply.get("status") or "sent",
            is_echo=False,
            media_id=event.get("media_id"),
            media_url=event.get("media_url"),
            mime_type=event.get("mime_type"),
            file_name=event.get("file_name"),
            caption=event.get("caption"),
            webhook_timestamp=_to_timestamp(event.get("timestamp")),
            message_json={"reply": reply, "source_event": event},
        )
        session.add(row)
        session.flush()
        return row
