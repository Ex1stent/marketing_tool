from __future__ import annotations
from typing import Any
from utils.logger import get_logger

logger = get_logger(__name__)


class InstaWebhookParser:
    def parse(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        logger.info("Insta Webhook Parser: %s", payload)

        if payload.get("object") != "instagram":
            return events

        for entry in payload.get("entry", []):
            account_id = entry.get("id")
            timestamp = entry.get("time")


            for messaging_event in entry.get("messaging", []):
                logger.info("Insta Webhook Parser: %s", messaging_event)
                
                if messaging_event.get("message"):
                    message = messaging_event["message"]

                    # Normalize event type
                    event_type = "message_echo" if message.get("is_echo") else "message"

                    events.append(
                        {
                            "platform": "instagram",
                            "event_type": event_type,
                            "account_id": account_id,
                            "sender_id": messaging_event.get("sender", {}).get("id"),
                            "recipient_id": messaging_event.get("recipient", {}).get("id"),
                            "message_id": message.get("mid"),
                            "text": message.get("text"),
                            "is_echo": message.get("is_echo", False),
                            "timestamp": messaging_event.get("timestamp", timestamp),
                            "raw_payload": messaging_event,
                        }
        )

            # for messaging_event in entry.get("messaging", []):
            #     logger.info("Insta Webhook Parser: %s", messaging_event)
            #     if messaging_event.get("message"):
            #         message = messaging_event.get("message", {})
            #         events.append(
            #             {
            #                 "platform": "instagram",
            #                 "event_type": "message",
            #                 "account_id": account_id,
            #                 "sender_id": messaging_event.get("sender", {}).get("id"),
            #                 "recipient_id": messaging_event.get("recipient", {}).get("id"),
            #                 "message_id": message.get("mid"),
            #                 "text": message.get("text"),
            #                 "timestamp": messaging_event.get("timestamp", timestamp),
            #                 "raw_payload": messaging_event,
            #             }
            #         )

            for change in entry.get("changes", []):
                if change.get("field") != "comments":
                    continue
                value = change.get("value", {})
                events.append(
                    {
                        "platform": "instagram",
                        "event_type": "comment",
                        "account_id": account_id,
                        "sender_id": value.get("from", {}).get("id"),
                        "recipient_id": None,
                        "message_id": None,
                        "comment_id": value.get("id"),
                        "media_id": value.get("media", {}).get("id"),
                        "text": value.get("text"),
                        "timestamp": value.get("created_time", timestamp),
                        "raw_payload": value,
                    }
                )
        return events
