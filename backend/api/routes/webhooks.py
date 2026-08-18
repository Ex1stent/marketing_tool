from __future__ import annotations

import json
from config import FACEBOOK_WEBHOOK_VERIFY_TOKEN, META_WEBHOOK_VERIFY_TOKEN, WHATSAPP_VERIFY_TOKEN

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from starlette.responses import PlainTextResponse

from models.engine import get_db
from webhooks.parsers.facebook_parser import FacebookWebhookParser
from webhooks.parsers.instagram_parser import InstagramWebhookParser
from webhooks.parsers.whatsapp_parser import WhatsappWebhookParser
from webhooks.processors.base import WebhookProcessor
from utils import logger

webhook_routes = APIRouter()


def _verify(request: Request, expected_token: str):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    if mode == "subscribe" and token and token == expected_token:
        return PlainTextResponse(challenge)
    raise HTTPException(status_code=403, detail="Webhook verification failed")


async def _handle_webhook(request: Request, label: str, parser_cls, db: Session) -> dict[str, str]:
    try:
        body = await request.body()
        payload = json.loads(body) if body else {}
    except json.JSONDecodeError:
        return {"status": "ok"}

    logger.info("%s webhook: %s", label, payload)
    try:
        await WebhookProcessor(db).process(payload, parser_cls())
    except Exception:
        logger.exception("%s webhook processing failed", label)
    return {"status": "ok"}


@webhook_routes.get("/meta/webhook")
async def insta_verify(request: Request):
    return _verify(request, META_WEBHOOK_VERIFY_TOKEN)


@webhook_routes.post("/meta/webhook")
async def insta_webhook(request: Request, db: Session = Depends(get_db)):
    return await _handle_webhook(request, "Instagram", InstagramWebhookParser, db)


@webhook_routes.get("/whatsapp/webhook")
async def whatsapp_verify(request: Request):
    return _verify(request, WHATSAPP_VERIFY_TOKEN)


@webhook_routes.post("/whatsapp/webhook")
async def whatsapp_webhook(request: Request, db: Session = Depends(get_db)):
    return await _handle_webhook(request, "WhatsApp", WhatsappWebhookParser, db)


@webhook_routes.get("/facebook/webhook")
async def facebook_verify(request: Request):
    return _verify(request, FACEBOOK_WEBHOOK_VERIFY_TOKEN)


@webhook_routes.post("/facebook/webhook")
async def facebook_webhook(request: Request, db: Session = Depends(get_db)):
    return await _handle_webhook(request, "Facebook", FacebookWebhookParser, db)
