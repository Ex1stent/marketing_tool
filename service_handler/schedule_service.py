from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from mcp.server.fastmcp import FastMCP

from models.database import SessionLocal
from models.scheduled_post import ScheduledPost
from scheduler.excel_parser import parse_excel
from utils.decorators import _tool
from utils.logger import get_logger

logger = get_logger(__name__)


def register_schedule_tools(mcp: FastMCP) -> None:
    tool = _tool(mcp)

    @tool
    def schedule_posts_from_excel(file_path: str) -> dict[str, Any]:
        """Parse an Excel sheet and schedule posts."""
        logger.info("schedule_posts_from_excel | file=%s", file_path)
        posts = parse_excel(file_path)

        session = SessionLocal()
        created = []
        try:
            for post in posts:
                row = ScheduledPost(
                    post_type=post["post_type"],
                    platform=post["platform"],
                    media_url=post["media_url"] or None,
                    message=post["message"] or None,
                    topic=post["topic"] or None,
                    recipient_id=post["recipient_id"] or None,
                    location_id=post["location_id"] or None,
                    scheduled_time=post["scheduled_time"],
                    status="pending",
                )
                session.add(row)
                session.flush()
                created.append({"id": row.id, "post_type": row.post_type,
                                "message": row.message, "topic": row.topic,
                                "scheduled_time": row.scheduled_time.isoformat()})
            session.commit()
            logger.info("Scheduled %d posts from Excel | file=%s", len(created), file_path)
        except Exception:
            session.rollback()
            logger.exception("Failed to schedule posts from Excel | file=%s", file_path)
            raise
        finally:
            session.close()

        return {"scheduled": len(created), "posts": created}

    @tool
    def list_scheduled_posts(status: str | None = None) -> list[dict[str, Any]]:
        """List all scheduled posts, optionally filtered by status (pending, scheduled, completed, failed, cancelled)."""
        session = SessionLocal()
        try:
            q = session.query(ScheduledPost)
            if status:
                q = q.filter(ScheduledPost.status == status)
            q = q.order_by(ScheduledPost.scheduled_time.asc())
            posts = [r.to_dict() for r in q.all()]
            logger.debug("list_scheduled_posts | status=%s count=%d", status, len(posts))
            return posts
        finally:
            session.close()

    @tool
    def cancel_scheduled_post(post_id: int) -> dict[str, Any]:
        """Cancel a pending scheduled post by ID."""
        session = SessionLocal()
        try:
            post = session.query(ScheduledPost).filter(ScheduledPost.id == post_id).first()
            if not post:
                logger.warning("cancel_scheduled_post | not found id=%d", post_id)
                return {"error": True, "message": f"No scheduled post with id {post_id}"}
            if post.status != "pending":
                logger.warning("cancel_scheduled_post | cannot cancel id=%d status=%s", post_id, post.status)
                return {"error": True, "message": f"Post {post_id} is '{post.status}', cannot cancel"}
            post.status = "cancelled"
            session.commit()
            logger.info("Cancelled scheduled post id=%d", post_id)
            return {"success": True, "message": f"Cancelled post {post_id}"}
        finally:
            session.close()

    @tool
    def update_scheduled_post(post_id: int, **kwargs: Any) -> dict[str, Any]:
        """Update a pending/scheduled post (scheduled_time, caption, message, media_url, etc.)."""
        allowed = {"post_type", "platform", "media_url", "message", "topic",
                    "recipient_id", "location_id", "scheduled_time"}
        session = SessionLocal()
        try:
            post = session.query(ScheduledPost).filter(ScheduledPost.id == post_id).first()
            if not post:
                logger.warning("update_scheduled_post | not found id=%d", post_id)
                return {"error": True, "message": f"No scheduled post with id {post_id}"}
            if post.status not in ("pending", "scheduled"):
                logger.warning("update_scheduled_post | cannot update id=%d status=%s", post_id, post.status)
                return {"error": True, "message": f"Post {post_id} is '{post.status}', cannot update"}
            updated = {k: v for k, v in kwargs.items() if k in allowed}
            for key, val in updated.items():
                setattr(post, key, val)
            session.commit()
            logger.info("Updated scheduled post id=%d fields=%s", post_id, set(updated))
            return {"success": True, "post": post.to_dict()}
        finally:
            session.close()

    @tool
    def get_scheduled_post_status(post_id: int) -> dict[str, Any]:
        """Check the execution status and result of a scheduled post."""
        session = SessionLocal()
        try:
            post = session.query(ScheduledPost).filter(ScheduledPost.id == post_id).first()
            if not post:
                logger.warning("get_scheduled_post_status | not found id=%d", post_id)
                return {"error": True, "message": f"No scheduled post with id {post_id}"}
            logger.debug("get_scheduled_post_status | id=%d status=%s", post_id, post.status)
            return post.to_dict()
        finally:
            session.close()

    
