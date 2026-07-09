from __future__ import annotations

import json
from typing import Any

from models.webhook_repository import WebhookRepository
from service_handler.providers import ModelProvider
from utils import graph
from utils.logger import get_logger

logger = get_logger(__name__)


class BaseWebhookProcessor:
    def __init__(self):
        self.repo = WebhookRepository()
        self.model = ModelProvider()

    async def _dispatch_reply(self, event: dict[str, Any], reply: dict[str, Any]) -> None:
        if event["platform"] == "instagram" and event["event_type"] in ("message"):
            await graph.post(
                f"{graph.ig_user_id()}/messages",
                recipient=json.dumps({"id": event["sender_id"]}),
                message=json.dumps({"text": reply.get("reply_text")}),
                messaging_type="RESPONSE",
            )
            return
        if event["platform"] == "instagram" and event["event_type"] in ("message_edit","message_echo"):
            return
        
        if event["platform"] == "instagram" and event["event_type"] == "comment":
            await graph.post(
                f"{event['comment_id']}/replies",
                message=reply["reply_text"],
            )
            return

        if event["platform"] == "whatsapp":
            await graph.whatsapp_post(
                f"{graph.whatsapp_id()}/messages",
                messaging_product="whatsapp",
                to=event["sender_id"],
                type="text",
                text={"body": reply.get("reply_text")},
            )
            return

        if event["platform"] == "facebook":
            await graph.facebook_post(
                f"{graph.facebook_page_id()}/messages",
                recipient={"id": event["sender_id"]},
                message={"text": reply.get("reply_text")},
                messaging_type="RESPONSE",
            )

    async def process(self, payload: dict[str, Any], parser) -> list[dict[str, Any]]:
        replies: list[dict[str, Any]] = []
        session = None

        try:
            events = parser.parse(payload)
            if not events:
                return replies

            session = self.repo.get_session()
            for event in events:
                self.repo.save_event(session, event)

                if not event.get("text"):
                    continue

                reply = self.model.classify_and_reply(
                    platform=event["platform"],
                    event_type=event["event_type"],
                    text=event["text"],
                )
                if not reply or not reply.get("should_reply"):
                    continue

                self.repo.save_reply(session, event.get("sender_id"), reply, event)
                replies.append(reply)
                await self._dispatch_reply(event, reply)

            session.commit()
            logger.info("Processed %s replies", len(replies))
            return replies
        except Exception:
            if session is not None:
                session.rollback()
            logger.exception("Webhook processing failed")
            raise
        finally:
            if session is not None:
                session.close()
