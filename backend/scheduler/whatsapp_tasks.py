from __future__ import annotations

from typing import Any

from celery_app import app
from mcp_.tools.whatsapp_service import send_whatsapp_image, send_whatsapp_message, send_whatsapp_video
from scheduler.task_utils import run_task_with_status
from utils.logger import logger


@app.task(bind=True, max_retries=3, default_retry_delay=30)
def whatsapp_message_task(self, number: str, message: str, post_id: int | None = None) -> dict[str, Any]:
    logger.info("whatsapp_message_task started | to=%s message=%s", number, message[:80] if message else None)
    result = run_task_with_status(self, post_id, send_whatsapp_message(number=number, message=message), "whatsapp_message_task")
    return {"success": True, "result": result}


@app.task(bind=True, max_retries=3, default_retry_delay=30)
def whatsapp_image_task(self, number: str, image_url: str, caption: str | None = None, post_id: int | None = None) -> dict[str, Any]:
    logger.info("whatsapp_image_task started | to=%s image_url=%s caption=%s", number, image_url[:60] if image_url else None, caption[:30] if caption else None)
    result = run_task_with_status(self, post_id, send_whatsapp_image(number=number, image_url=image_url, caption=caption), "whatsapp_image_task")
    return {"success": True, "result": result}


@app.task(bind=True, max_retries=3, default_retry_delay=30)
def whatsapp_video_task(self, number: str, video_url: str, caption: str | None = None, post_id: int | None = None) -> dict[str, Any]:
    logger.info("whatsapp_video_task started | to=%s video_url=%s caption=%s", number, video_url[:60] if video_url else None, caption[:30] if caption else None)
    result = run_task_with_status(self, post_id, send_whatsapp_video(number=number, video_url=video_url, caption=caption), "whatsapp_video_task")
    return {"success": True, "result": result}
