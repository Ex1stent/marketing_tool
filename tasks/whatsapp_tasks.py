from __future__ import annotations

from typing import Any

import httpx

from celery_app import app
from config import IG_GRAPH_HOST, IG_GRAPH_VERSION, WHATSAPP_ID, WHATSAPP_TOKEN
from utils import graph
from utils.logger import get_logger

logger = get_logger(__name__)


def _whatsapp_post(path: str, **fields: Any) -> Any:
    base = f"https://{IG_GRAPH_HOST}/{IG_GRAPH_VERSION}"
    r = httpx.post(
        f"{base}/{path.lstrip('/')}",
        params={"access_token": WHATSAPP_TOKEN},
        json={k: v for k, v in fields.items() if v is not None},
        timeout=30.0,
    )
    body = r.json() if r.text else r.text
    if r.status_code >= 400:
        raise graph.GraphError(r.status_code, body)
    return body


@app.task(bind=True, max_retries=3, default_retry_delay=30)
def whatsapp_message_task(self, number: str, message: str) -> dict[str, Any]:
    logger.info("whatsapp_message_task started | to=%s message=%s", number, message[:80] if message else None)
    try:
        result = _whatsapp_post(
            f"{WHATSAPP_ID}/messages",
            messaging_product="whatsapp",
            to=number,
            type="text",
            text={"body": message},
        )
        logger.info("whatsapp_message_task completed")
        return {"success": True, "result": result}
    except Exception as exc:
        logger.warning("whatsapp_message_task failed | attempt=%d error=%s", self.request.retries + 1, exc)
        raise self.retry(exc=exc)


@app.task(bind=True, max_retries=3, default_retry_delay=30)
def whatsapp_image_task(self, number: str, image_url: str, caption: str | None = None) -> dict[str, Any]:
    logger.info("whatsapp_image_task started | to=%s image_url=%s caption=%s", number, image_url[:60] if image_url else None,caption[:30] if caption else None)
    try:
        image = {"link": image_url}
        if caption:
            image["caption"] = caption
        result = _whatsapp_post(
            f"{WHATSAPP_ID}/messages",
            messaging_product="whatsapp",
            to=number,
            type="image",
            image=image,
        )
        logger.info("whatsapp_image_task completed")
        return {"success": True, "result": result}
    except Exception as exc:
        logger.warning("whatsapp_image_task failed | attempt=%d error=%s", self.request.retries + 1, exc)
        raise self.retry(exc=exc)


@app.task(bind=True, max_retries=3, default_retry_delay=30)
def whatsapp_video_task(self, number: str, video_url: str, caption: str | None = None) -> dict[str, Any]:
    logger.info("whatsapp_video_task started | to=%s video_url=%s caption=%s", number, video_url[:60] if video_url else None,caption[:30] if caption else None)
    try:
        video = {"link": video_url}
        if caption:
            video["caption"] = caption
        result = _whatsapp_post(
            f"{WHATSAPP_ID}/messages",
            messaging_product="whatsapp",
            to=number,
            type="video",
            video=video,
        )
        logger.info("whatsapp_video_task completed")
        return {"success": True, "result": result}
    except Exception as exc:
        logger.warning("whatsapp_video_task failed | attempt=%d error=%s", self.request.retries + 1, exc)
        raise self.retry(exc=exc)
