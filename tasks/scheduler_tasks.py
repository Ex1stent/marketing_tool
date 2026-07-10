from __future__ import annotations

from datetime import datetime, timezone

from celery_app import app
from models.database import SessionLocal
from models.scheduled_post_repository import ScheduledPostRepository
from utils.logger import get_logger

logger = get_logger(__name__)


@app.task
def check_and_enqueue_posts() -> dict[str, int]:
    from tasks.instagram_tasks import publish_carousel_task, publish_image_task, publish_reel_task, publish_story_task
    from tasks.whatsapp_tasks import whatsapp_message_task, whatsapp_image_task, whatsapp_video_task
    from tasks.facebook_tasks import create_page_post_task

    TASK_MAP = {
        "image": publish_image_task,
        "reel": publish_reel_task,
        "story": publish_story_task,
        "carousel": publish_carousel_task,
        "whatsapp_text": whatsapp_message_task,
        "whatsapp_image": whatsapp_image_task,
        "whatsapp_video": whatsapp_video_task,
        "facebook_post": create_page_post_task,
    }

    session = SessionLocal()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    repo = ScheduledPostRepository()
    dispatched = 0
    errors = 0

    try:
        posts = (
            session.query(repo.model)
            .filter(repo.model.status == "pending", repo.model.scheduled_time <= now)
            .all()
        )

        if not posts:
            logger.debug("No pending posts due")
            return {"dispatched": 0, "errors": 0}

        logger.info("check_and_enqueue_posts found %d due posts", len(posts))

        for post in posts:
            task_func = TASK_MAP.get(post.post_type)
            if not task_func:
                logger.warning("Unknown post_type=%s for post id=%d", post.post_type, post.id)
                post.status = "failed"
                post.error_message = f"Unknown post_type: {post.post_type}"
                session.flush()
                errors += 1
                continue

            task_kwargs = {}
            if post.post_type == "image":
                task_kwargs = {"image_url": post.media_url, "caption": post.message, "location_id": post.location_id}
            elif post.post_type == "reel":
                task_kwargs = {"video_url": post.media_url, "caption": post.message}
            elif post.post_type == "story":
                task_kwargs = {"image_url": post.media_url, "video_url": None}
            elif post.post_type == "whatsapp_text":
                task_kwargs = {"number": post.recipient_id, "message": post.message}
            elif post.post_type == "whatsapp_image":
                task_kwargs = {"number": post.recipient_id, "image_url": post.media_url, "caption": post.message}
            elif post.post_type == "whatsapp_video":
                task_kwargs = {"number": post.recipient_id, "video_url": post.media_url, "caption": post.message}
            elif post.post_type == "facebook_post":
                task_kwargs = {"image_url": post.media_url, "message": post.message}

            task = task_func.delay(**task_kwargs)
            post.task_id = task.id
            post.status = "scheduled"
            session.flush()
            dispatched += 1
            logger.info("Dispatched post id=%d type=%s task_id=%s", post.id, post.post_type, task.id)

        session.commit()
        logger.info("check_and_enqueue_posts done | dispatched=%d errors=%d", dispatched, errors)
    except Exception:
        session.rollback()
        logger.exception("check_and_enqueue_posts failed")
        raise
    finally:
        session.close()

    return {"dispatched": dispatched, "errors": errors}
