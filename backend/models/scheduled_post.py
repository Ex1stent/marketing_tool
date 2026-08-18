from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from models.engine import SessionLocal, TableScheduledPost, row_to_dict, rows_to_dicts, set_model_fields
from utils.logger import logger


class ScheduledPostRepository:
    def __init__(self, session: Session):
        self.session = session
        self.model = TableScheduledPost
        

    def create_scheduled_post(self, payload):
        model_obj = self.model()
        set_model_fields(self.session, model_obj, payload)
        return model_obj

    def get_due_posts(self, cutoff: datetime) -> list[Any]:
        return (
            self.session.query(self.model)
            .filter(self.model.status == "pending", self.model.scheduled_time <= cutoff)
            .all()
        )

    def mark_scheduled(self, post, task_id: str) -> None:
        post.task_id = task_id
        post.status = "scheduled"
        self.session.flush()

    def mark_failed(self, post, reason: str) -> None:
        logger.error("Scheduled post %d failed | reason=%s", post.id, reason)
        post.status = "failed"
        self.session.flush()

    def get_post_for_update(self, post_id: int, allowed_statuses: set[str]):
        # Find post and validate status. Returns None if not found, raises ValueError if status not allowed.
        post = self.session.query(self.model).filter(self.model.id == post_id).first()
        if not post:
            return None
        if post.status not in allowed_statuses:
            raise ValueError(f"Post {post_id} is '{post.status}', cannot update")
        return post

    def dispatch_post(self, post):
        # Dispatch a single post to its celery task. Returns (success, error_message).
        from scheduler.scheduler_tasks import _TASK_MAP, build_kwargs

        task_fn = _TASK_MAP.get(post.post_type)
        if not task_fn:
            self.mark_failed(post, f"Unknown post_type: {post.post_type}")
            return False, f"Unknown post_type: {post.post_type}"
        try:
            kwargs = build_kwargs(post)
            task = task_fn.delay(**kwargs)
        except Exception as e:
            self.mark_failed(post, str(e))
            return False, str(e)
        self.mark_scheduled(post, task.id)
        return True, ""

    # @classmethod
    # def update_post_status(cls, post_id: int, status: str, error_message: str = "") -> None:
    #     session = SessionLocal()
    #     try:
    #         post = session.query(TableScheduledPost).filter_by(id=post_id).first()
    #         if post:
    #             post.status = status
    #             if error_message:
    #                 post.error_message = error_message
    #         session.commit()
    #     except Exception as e:
    #         session.rollback()
    #         logger.exception("Failed to update post status %s | post_id=%d", e, post_id)
    #     finally:
    #         session.close()

    def save(self):
        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            logger.exception("Failed to save scheduled post %s", e)

    def to_dict(self, row: Any) -> dict[str, Any]:
        return row_to_dict(row)

    def to_dicts(self, rows: list[Any]) -> list[dict[str, Any]]:
        return rows_to_dicts(rows)


def update_post_status(post_id: int, status: str, error_message: str = "") -> None:
    session = SessionLocal()
    try:
        post = session.query(TableScheduledPost).filter_by(id=post_id).first()
        if post:
            post.status = status
            if error_message:
                post.error_message = error_message
        session.commit()
    except Exception as e:
        logger.exception("Failed to update post status %s | post_id=%d", e, post_id)
    finally:
        session.close()
