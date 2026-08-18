from __future__ import annotations

from typing import Any

from celery_app import app
from mcp_.tools.insta_service import publish_carousel, publish_image, publish_reel, publish_story
from scheduler.task_utils import run_task_with_status
from utils.logger import logger


@app.task(bind=True, max_retries=2, default_retry_delay=30)
def publish_image_task(self, image_url: str, caption: str | None = None, location_id: str | None = None, post_id: int | None = None) -> dict[str, Any]:
    logger.info("publish_image_task started | image_url=%s caption=%s", image_url[:60] if image_url else None, caption)
    result = run_task_with_status(self, post_id, publish_image(image_url=image_url, caption=caption, location_id=location_id), "publish_image_task")
    return {"success": True, "media_id": result.get("id"), "result": result}


@app.task(bind=True, max_retries=2, default_retry_delay=60)
def publish_reel_task(self, video_url: str, caption: str | None = None, share_to_feed: bool = True, cover_url: str | None = None, post_id: int | None = None) -> dict[str, Any]:
    logger.info("publish_reel_task started | video_url=%s caption=%s", video_url[:60] if video_url else None, caption)
    result = run_task_with_status(self, post_id, publish_reel(video_url=video_url, caption=caption, share_to_feed=share_to_feed, cover_url=cover_url), "publish_reel_task")
    return {"success": True, "media_id": result.get("id"), "result": result}


@app.task(bind=True, max_retries=3, default_retry_delay=30)
def publish_story_task(self, video_url: str | None = None, post_id: int | None = None, **kwargs: Any) -> dict[str, Any]:
    image_url = kwargs.get("image_url")
    logger.info("publish_story_task started | image_url=%s video_url=%s", bool(image_url), bool(video_url))
    result = run_task_with_status(self, post_id, publish_story(image_url=image_url, video_url=video_url), "publish_story_task")
    return {"success": True, "media_id": result.get("id"), "result": result}


@app.task(bind=True, max_retries=3, default_retry_delay=60)
def publish_carousel_task(self, items: list[dict[str, str]], caption: str | None = None, post_id: int | None = None) -> dict[str, Any]:
    logger.info("publish_carousel_task started | items=%d caption=%s", len(items), caption)
    result = run_task_with_status(self, post_id, publish_carousel(items=items, caption=caption), "publish_carousel_task")
    return {"success": True, "media_id": result.get("id"), "result": result}
