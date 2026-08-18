from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from models.webhook_post import WebhookRepository, _to_timestamp
from services.ai_reply_service import AIReplyService
from utils import graph
from utils.logger import logger


class WebhookProcessor:
    def __init__(self, session: Session):
        self.repo = WebhookRepository(session)
        self.ai = AIReplyService()



    async def process(self, payload, parser):
        try:
            events = self._parse_events(payload, parser)
            if not events:
                return []

            replies = []
            for event in events:
                if event.get("event_type") in ("message_echo","message_edit"):
                    continue
                # Save inbound webhook event
                inbound_data=self._build_inbound_event(event)
                self.repo.add_event(inbound_data)
                
                # Generate AI reply if applicable
                reply = self._maybe_generate_reply(event)
                if not reply:
                    logger.info("No reply generated for %s event from %s", event.get("platform"), event.get("sender_id"))
                    continue

                print("generated_reply: ",reply)

                # Send reply first (payload only exists after dispatch)
                response, sent_payload = await self._dispatch_reply(event, reply)
                sent_message_id = self.extract_sent_message_id(event, response) if response else None

                # Build outbound with both text and raw sending payload
                outbound = self._build_outbound_reply(event, reply, sent_payload, sent_message_id)
                outbound_model = self.repo.add_event(outbound)

                replies.append(reply)

            self.repo.save_event()
            return replies

        except Exception as e:
            logger.exception(f"Webhook processing failed, {str(e)}")
            raise
        
    def _maybe_generate_reply(self, event):
        reply = self.ai.classify_and_reply(event["platform"], event["event_type"], event.get("text"))
        if not reply or not (reply.get("should_reply") or reply.get("reply_text")):
            return None
        return reply
        
    
    def _parse_events(self, payload, parser):
        events = parser.parse(payload)
        return events

    
    def _build_inbound_event(self, event):
        inbound_event = dict(event)
        inbound_event["direction"] = "inbound"
        inbound_event["status"] = "received"
        inbound_event["timestamp"] = _to_timestamp(inbound_event["timestamp"])
        inbound_event["message_json"] = inbound_event.pop("raw_payload")
        return inbound_event

    def _build_outbound_reply(self, event, reply, sent_payload=None, sent_message_id=None):
        return {
            "direction": "outbound",
            "status": "sent",
            "platform": event.get("platform"),
            "sender_id": event.get("sender_id"),
            "recipient_id": event.get("recipient_id"),
            "timestamp": _to_timestamp(event.get("timestamp")),
            "text": reply.get("reply_text"),
            "message_json": sent_payload,
            "message_id": sent_message_id,
        }

    async def _dispatch_reply(self, event: dict[str, Any], reply: dict[str, Any]) -> tuple[Any, dict | None]:
        platform = event.get("platform")
        if platform == "instagram":
            return await self._send_instagram_reply(event, reply)
        elif platform == "facebook":
            return await self._send_facebook_reply(event, reply)
        elif platform == "whatsapp":
            return await self._send_whatsapp_reply(event, reply)
        else:
            logger.warning("Unsupported platform: %s", platform)
            return None, None

    async def _send_instagram_reply(self, event: dict[str, Any], reply: dict[str, Any]) -> tuple[Any, dict | None]:
        event_type = event.get("event_type")
        if event_type == "message":
            payload = {
                "recipient": {"id": event["sender_id"]},
                "message": {"text": reply["reply_text"]},
                "messaging_type": "RESPONSE",
            }
            print(payload)
            return await graph.post(f"{graph.ig_user_id()}/messages", **payload), payload
        elif event_type == "comment":
            payload = {"message": reply["reply_text"]}
            return await graph.post(f"{event['comment_id']}/replies", **payload), payload
        elif event_type in {"message_edit", "message_echo"}:
            return None, None
        else:
            logger.warning("Unsupported Instagram event type: %s", event_type)
            return None, None

    async def _send_whatsapp_reply(self, event: dict[str, Any], reply: dict[str, Any]) -> tuple[Any, dict]:
        payload = {
            "messaging_product": "whatsapp",
            "to": event["sender_id"],
            "type": "text",
            "text": json.dumps({"body": reply["reply_text"]}),
        }
        return await graph.whatsapp_post(
            f"{graph.whatsapp_id()}/messages", **payload
        ), payload

    async def _send_facebook_reply(self, event: dict[str, Any], reply: dict[str, Any]) -> tuple[Any, dict]:
        payload = {
            "recipient": json.dumps({"id": event["sender_id"]}),
            "message": json.dumps({"text": reply["reply_text"]}),
            "messaging_type": "RESPONSE",
        }
        return await graph.facebook_post(f"{graph.facebook_page_id()}/messages", **payload), payload
    
    def extract_sent_message_id(self, event,response):
        platform = event.get("platform")
        if platform == "whatsapp":
            msgs = response.get("messages", [])
            return msgs[0]["id"] if msgs else None  
        if platform in ("instagram", "facebook"):
            return response.get("message_id") or response.get("id") 
        return None
    

