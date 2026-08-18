from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from celery_app import app
from models.engine import SessionLocal
from models.scheduled_post import ScheduledPostRepository
from utils.logger import logger

from scheduler.facebook_tasks import create_page_post_task
from scheduler.instagram_tasks import publish_carousel_task, publish_image_task, publish_reel_task, publish_story_task
from scheduler.whatsapp_tasks import whatsapp_image_task, whatsapp_message_task, whatsapp_video_task

_FIELD_MAPPINGS: dict[str, dict[str, str]] = {
    "instagram_image":    {"media_url": "image_url", "message": "caption"},
    "instagram_reel":     {"media_url": "video_url", "message": "caption"},
    "instagram_story":    {"media_url": "image_url"},
    "instagram_carousel": {"message": "caption"},
    "whatsapp_text":      {"recipient_id": "number", "message": "message"},
    "whatsapp_image":     {"recipient_id": "number", "media_url": "image_url", "message": "caption"},
    "whatsapp_video":     {"recipient_id": "number", "media_url": "video_url", "message": "caption"},
    "facebook_post":      {"message": "message", "media_url": "image_url"},
}


def build_kwargs(post: Any) -> dict[str, Any]:
    kwargs: dict[str, Any] = {"post_id": post.id}

    field_map = _FIELD_MAPPINGS.get(post.post_type, {})
    for post_field, task_param in field_map.items():
        value = getattr(post, post_field, None)
        if value is not None:
            kwargs[task_param] = value

    if post.post_type == "instagram_carousel":
        items_raw = getattr(post, "items", None)
        if items_raw:
            kwargs["items"] = json.loads(items_raw) if isinstance(items_raw, str) else items_raw

    return kwargs




_TASK_MAP: dict[str, Any] = {
    "instagram_image":    publish_image_task,
    "instagram_reel":     publish_reel_task,
    "instagram_story":    publish_story_task,
    "instagram_carousel": publish_carousel_task,
    "whatsapp_text":      whatsapp_message_task,
    "whatsapp_image":     whatsapp_image_task,
    "whatsapp_video":     whatsapp_video_task,
    "facebook_post":      create_page_post_task,
}


@app.task
def check_and_enqueue_posts() -> dict[str, int]:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    session = SessionLocal()
    dispatched = 0
    errors = 0

    try:
        repo = ScheduledPostRepository(session)
        posts = repo.get_due_posts(now)
        if not posts:
            logger.debug("No pending posts due")
            return {"dispatched": 0, "errors": 0}

        for post in posts:
            ok, _ = repo.dispatch_post(post)
            if ok:
                dispatched += 1
            else:
                errors += 1
        repo.save()
        logger.info("check_and_enqueue_posts done | dispatched=%d errors=%d", dispatched, errors)
    except Exception:
        logger.exception("check_and_enqueue_posts failed")
        raise
    finally:
        session.close()

    return {"dispatched": dispatched, "errors": errors}
