from __future__ import annotations

from typing import Any

from utils.logger import logger


class FacebookWebhookParser:
    def _parse_messaging(self, value: list[dict[str, Any]], page_id: str, timestamp: Any) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        for messaging_event in value:
            if messaging_event.get("message"):
                msg = messaging_event["message"]
                events.append(
                    {
                        "platform": "facebook",
                        "event_type": "message",
                        "account_id": page_id,
                        "sender_id": messaging_event.get("sender", {}).get("id"),
                        "recipient_id": messaging_event.get("recipient", {}).get("id"),
                        "message_id": msg.get("mid"),
                        "text": msg.get("text"),
                        "is_echo": msg.get("is_echo", False),
                        "timestamp": messaging_event.get("timestamp", timestamp),
                        "raw_payload": messaging_event,
                    }
                )
            if messaging_event.get("postback"):
                postback = messaging_event["postback"]
                events.append(
                    {
                        "platform": "facebook",
                        "event_type": "postback",
                        "account_id": page_id,
                        "sender_id": messaging_event.get("sender", {}).get("id"),
                        "recipient_id": messaging_event.get("recipient", {}).get("id"),
                        "message_id": None,
                        "text": postback.get("payload"),
                        "is_echo": False,
                        "timestamp": messaging_event.get("timestamp", timestamp),
                        "raw_payload": messaging_event,
                    }
                )
        return events

    def _parse_changes(self, changes: list[dict[str, Any]], page_id: str, timestamp: Any) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        for change in changes:
            field = change.get("field")
            value = change.get("value", {})
            if field == "feed":
                events.append(
                    {
                        "platform": "facebook",
                        "event_type": "feed",
                        "account_id": page_id,
                        "sender_id": value.get("from", {}).get("id"),
                        "recipient_id": page_id,
                        "message_id": value.get("post_id"),
                        "text": value.get("message"),
                        "timestamp": value.get("created_time", timestamp),
                        "raw_payload": value,
                    }
                )
            elif field == "comments":
                events.append(
                    {
                        "platform": "facebook",
                        "event_type": "comment",
                        "account_id": page_id,
                        "sender_id": value.get("from", {}).get("id"),
                        "recipient_id": page_id,
                        "message_id": value.get("comment_id"),
                        "comment_id": value.get("comment_id"),
                        "media_id": value.get("post_id"),
                        "text": value.get("message"),
                        "timestamp": value.get("created_time", timestamp),
                        "raw_payload": value,
                    }
                )
        return events

    def parse(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        if payload.get("object") != "page":
            return events
        for entry in payload.get("entry", []):
            page_id = entry.get("id")
            timestamp = entry.get("time")
            events.extend(self._parse_messaging(entry.get("messaging", []), page_id, timestamp))
            events.extend(self._parse_changes(entry.get("changes", []), page_id, timestamp))
        logger.info("Facebook webhook parsed | events=%d", len(events))
        return events
