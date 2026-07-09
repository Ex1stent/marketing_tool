from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, Request
from starlette.responses import PlainTextResponse

from config import FACEBOOK_WEBHOOK_VERIFY_TOKEN, META_WEBHOOK_VERIFY_TOKEN, WHATSAPP_VERIFY_TOKEN
from service_handler.facebook_webhook_processor import FacebookWebhookProcessor
from service_handler.insta_webhook_processor import InstaWebhookProcessor
from service_handler.whatsapp_webhook_processor import WhatsappWebhookProcessor
from utils import logger

webhook_routes = APIRouter()


@webhook_routes.get("/meta/webhook")
async def insta_verify(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    if mode == "subscribe" and token and token == META_WEBHOOK_VERIFY_TOKEN:
        return PlainTextResponse(challenge)
    raise HTTPException(status_code=403, detail="Webhook verification failed")


@webhook_routes.post("/meta/webhook")
async def insta_webhook(request: Request):
    try:
        body = await request.body()
        payload = json.loads(body) if body else {}
    except json.JSONDecodeError:
        return {"status": "ok"}
    logger.info("Instagram webhook: %s", payload)
    try:
        await InstaWebhookProcessor().process(payload)
    except Exception:
        logger.exception("Instagram webhook processing failed")
    return {"status": "ok"}


@webhook_routes.get("/whatsapp/webhook")
async def whatsapp_verify(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    if mode == "subscribe" and token == WHATSAPP_VERIFY_TOKEN:
        return PlainTextResponse(challenge)
    raise HTTPException(status_code=403, detail="Webhook verification failed")


@webhook_routes.post("/whatsapp/webhook")
async def whatsapp_webhook(request: Request):
    try:
        body = await request.body()
        payload = json.loads(body) if body else {}
    except json.JSONDecodeError:
        return {"status": "ok"}
    logger.info("WhatsApp webhook: %s", payload)
    try:
        await WhatsappWebhookProcessor().process(payload)
    except Exception:
        logger.exception("WhatsApp webhook processing failed")
    return {"status": "ok"}


@webhook_routes.get("/facebook/webhook")
async def facebook_verify(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    if mode == "subscribe" and token and token == FACEBOOK_WEBHOOK_VERIFY_TOKEN:
        return PlainTextResponse(challenge)
    raise HTTPException(status_code=403, detail="Webhook verification failed")


@webhook_routes.post("/facebook/webhook")
async def facebook_webhook(request: Request):
    try:
        body = await request.body()
        payload = json.loads(body) if body else {}
    except json.JSONDecodeError:
        return {"status": "ok"}
    logger.info("Facebook webhook: %s", payload)
    try:
        await FacebookWebhookProcessor().process(payload)
    except Exception:
        logger.exception("Facebook webhook processing failed")
    return {"status": "ok"}
