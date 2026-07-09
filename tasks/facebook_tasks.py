from __future__ import annotations

from typing import Any

import httpx

from celery_app import app
from config import FACEBOOK_ACCESS_TOKEN, FACEBOOK_GRAPH_HOST, FACEBOOK_GRAPH_VERSION, FACEBOOK_PAGE_ID
from utils import graph
from utils.logger import get_logger

logger = get_logger(__name__)


def _facebook_post(path: str, **fields: Any) -> Any:
    base = f"https://{FACEBOOK_GRAPH_HOST}/{FACEBOOK_GRAPH_VERSION}"
    r = httpx.post(
        f"{base}/{path.lstrip('/')}",
        params={"access_token": FACEBOOK_ACCESS_TOKEN},
        data={k: v for k, v in fields.items() if v is not None},
        timeout=30.0,
    )
    body = r.json() if r.text else r.text
    if r.status_code >= 400:
        raise graph.GraphError(r.status_code, body)
    return body


@app.task(bind=True, max_retries=3, default_retry_delay=30)
def create_page_post_task(self, message: str, image_url: str | None = None) -> dict[str, Any]:
    logger.info("create_page_post_task started | message=%s image_url=%s", message[:80] if message else None, image_url)
    try:
        if image_url:
            result = _facebook_post(f"{FACEBOOK_PAGE_ID}/photos", url=image_url, message=message)
        else:
            result = _facebook_post(f"{FACEBOOK_PAGE_ID}/feed", message=message)
        logger.info("create_page_post_task completed | post_id=%s", result.get("id"))
        return {"success": True, "post_id": result.get("id"), "result": result}
    except Exception as exc:
        logger.warning("create_page_post_task failed | attempt=%d error=%s", self.request.retries + 1, exc)
        raise self.retry(exc=exc)


@app.task(bind=True, max_retries=3, default_retry_delay=30)
def send_page_message_task(self, recipient_id: str, text: str) -> dict[str, Any]:
    logger.info("send_page_message_task started | recipient=%s text=%s", recipient_id, text[:80] if text else None)
    try:
        result = _facebook_post(
            f"{FACEBOOK_PAGE_ID}/messages",
            recipient={"id": recipient_id},
            message={"text": text},
            messaging_type="RESPONSE",
        )
        logger.info("send_page_message_task completed")
        return {"success": True, "result": result}
    except Exception as exc:
        logger.warning("send_page_message_task failed | attempt=%d error=%s", self.request.retries + 1, exc)
        raise self.retry(exc=exc)
