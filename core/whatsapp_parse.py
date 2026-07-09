from __future__ import annotations

from typing import Any
from utils.logger import get_logger

logger = get_logger(__name__)

class WhatsappWebhookParser:
    def parse(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        logger.info("Whatsapp Webhook Parser: %s", payload)
        if payload.get("object") != "whatsapp_business_account":
            return events

        for entry in payload.get("entry", []):
            account_id = entry.get("id")
            for change in entry.get("changes", []):
                value = change.get("value", {})
                for message in value.get("messages", []):
                    if message.get("type") != "text":
                        continue
                    events.append(
                        {
                            "platform": "whatsapp",
                            "event_type": "message",
                            "account_id": account_id,
                            "sender_id": message.get("from"),
                            "recipient_id": value.get("metadata", {}).get("phone_number_id"),
                            "message_id": message.get("id"),
                            "text": message.get("text", {}).get("body"),
                            "timestamp": message.get("timestamp"),
                            "raw_payload": message,
                        }
                    )

        logger.info("Whatsapp Webhook Events: %s", events)
        return events
