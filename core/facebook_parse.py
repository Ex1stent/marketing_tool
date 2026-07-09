from __future__ import annotations

from typing import Any

from utils.logger import get_logger

logger = get_logger(__name__)


class FacebookWebhookParser:
    def parse(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        if payload.get("object") != "page":
            logger.debug("Facebook webhook ignored | object=%s", payload.get("object"))
            return events

        for entry in payload.get("entry", []):
            page_id = entry.get("id")
            timestamp = entry.get("time")

            for messaging_event in entry.get("messaging", []):
                sender_id = messaging_event.get("sender", {}).get("id")
                recipient_id = messaging_event.get("recipient", {}).get("id")

                if messaging_event.get("message"):
                    msg = messaging_event["message"]
                    events.append({
                        "platform": "facebook",
                        "event_type": "message",
                        "account_id": page_id,
                        "sender_id": sender_id,
                        "recipient_id": recipient_id,
                        "message_id": msg.get("mid"),
                        "text": msg.get("text"),
                        "is_echo": msg.get("is_echo", False),
                        "timestamp": messaging_event.get("timestamp", timestamp),
                        "raw_payload": messaging_event,
                    })

                if messaging_event.get("postback"):
                    events.append({
                        "platform": "facebook",
                        "event_type": "postback",
                        "account_id": page_id,
                        "sender_id": sender_id,
                        "recipient_id": recipient_id,
                        "message_id": None,
                        "text": messaging_event["postback"].get("payload", ""),
                        "is_echo": False,
                        "timestamp": messaging_event.get("timestamp", timestamp),
                        "raw_payload": messaging_event,
                    })

            for change in entry.get("changes", []):
                value = change.get("value", {})
                field = change.get("field")

                if field == "feed":
                    events.append({
                        "platform": "facebook",
                        "event_type": "feed",
                        "account_id": page_id,
                        "sender_id": value.get("from", {}).get("id"),
                        "recipient_id": page_id,
                        "message_id": value.get("post_id"),
                        "text": value.get("message", ""),
                        "is_echo": False,
                        "timestamp": value.get("created_time", timestamp),
                        "raw_payload": value,
                    })

                if field == "comments":
                    events.append({
                        "platform": "facebook",
                        "event_type": "comment",
                        "account_id": page_id,
                        "sender_id": value.get("from", {}).get("id"),
                        "recipient_id": page_id,
                        "message_id": value.get("comment_id"),
                        "comment_id": value.get("comment_id"),
                        "media_id": value.get("post_id"),
                        "text": value.get("message", ""),
                        "is_echo": False,
                        "timestamp": value.get("created_time", timestamp),
                        "raw_payload": value,
                    })

        logger.info("Facebook webhook parsed | object=page entries=%d events=%d", len(payload.get("entry", [])), len(events))
        return events
