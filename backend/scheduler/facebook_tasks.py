from __future__ import annotations

from typing import Any

from celery_app import app
from mcp_.tools.facebook_service import create_page_post, send_page_message
from scheduler.task_utils import run_task_with_status
from utils.logger import logger


@app.task(bind=True, max_retries=3, default_retry_delay=30)
def create_page_post_task(self, message: str, image_url: str | None = None, post_id: int | None = None) -> dict[str, Any]:
    logger.info("create_page_post_task started | message=%s image_url=%s", message[:80] if message else None, image_url)
    result = run_task_with_status(self, post_id, create_page_post(message=message, image_url=image_url), "create_page_post_task")
    return {"success": True, "post_id": result.get("id"), "result": result}


@app.task(bind=True, max_retries=3, default_retry_delay=30)
def send_page_message_task(self, recipient_id: str, text: str, post_id: int | None = None) -> dict[str, Any]:
    logger.info("send_page_message_task started | recipient=%s text=%s", recipient_id, text[:80] if text else None)
    result = run_task_with_status(self, post_id, send_page_message(recipient_id=recipient_id, text=text), "send_page_message_task")
    return {"success": True, "result": result}
