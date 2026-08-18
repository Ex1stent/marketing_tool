from __future__ import annotations

from typing import Any

from models.engine import SessionLocal, row_to_dict
from models.scheduled_post import ScheduledPostRepository
from service_handler.scheduler_handler import SchedulerHandler
from utils.decorators import _tool
from mcp.server.fastmcp import FastMCP


def register_schedule_tools(mcp: FastMCP) -> None:
    tool = _tool(mcp)

    @tool
    def schedule_posts_from_excel(file_path: str) -> dict[str, Any]:
        """Parse an Excel sheet and schedule the posts it describes.

        Args:
            file_path: Path to the Excel file containing the posts to schedule.

        Returns:
            Result of the scheduling operation as a dict.
        """
        session = SessionLocal()
        try:
            return SchedulerHandler(session).schedule_from_path(file_path)
        finally:
            session.close()

    @tool
    def list_scheduled_posts(status: str | None = None) -> list[dict[str, Any]]:
        """List all scheduled posts, optionally filtered by status.

        Args:
            status: Optional status to filter by (e.g. pending, scheduled,
                published).

        Returns:
            list of scheduled post dicts.
        """
        session = SessionLocal()
        try:
            return SchedulerHandler(session).list_posts(status)
        finally:
            session.close()

    @tool
    def cancel_scheduled_post(post_id: int) -> dict[str, Any]:
        """Cancel a pending scheduled post by its ID.

        Args:
            post_id: ID of the scheduled post to cancel.

        Returns:
            dict describing the result of the cancellation.
        """
        session = SessionLocal()
        try:
            return SchedulerHandler(session).cancel_post(post_id)
        finally:
            session.close()

    @tool
    def update_scheduled_post(post_id: int, **kwargs: Any) -> dict[str, Any]:
        """Update a pending or scheduled post by ID.

        Args:
            post_id: ID of the scheduled post to update.
            kwargs: Key-value pairs of fields to update on the post.

        Returns:
            dict describing the updated post or the result of the update.
        """
        session = SessionLocal()
        try:
            return SchedulerHandler(session).update_post(post_id, **kwargs)
        finally:
            session.close()

    @tool
    def get_scheduled_post_status(post_id: int) -> dict[str, Any]:
        """Check the execution status and result of a scheduled post.

        Args:
            post_id: ID of the scheduled post to inspect.

        Returns:
            dict with the post's current status and execution result.
        """
        session = SessionLocal()
        try:
            repo = ScheduledPostRepository(session)
            post = session.query(repo.model).filter(repo.model.id == post_id).first()
            if not post:
                return {"error": True, "message": f"No scheduled post with id {post_id}"}
            return row_to_dict(post)
        finally:
            session.close()
