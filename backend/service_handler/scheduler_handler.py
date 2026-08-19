from __future__ import annotations

import os
from typing import Any

from fastapi import HTTPException, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session
from celery_app import app

from models.engine import TableScheduledPost, TableScheduledPostBatch, rows_to_dicts
from models.scheduled_post import ScheduledPostRepository
from models.scheduled_post_batch import ScheduledPostBatchRepository
from service_handler.file_upload_handler import FileUploadHandler
from services.excel_parser import parse_excel
from utils.logger import logger


class SchedulerHandler:

    def __init__(self, db: Session):
        self.db = db

    def get_stats(self) -> dict[str, Any]:
        # Return post counts grouped by status.
        try:
            model = TableScheduledPost
            rows = (
                self.db.query(model.status, func.count())
                .join(TableScheduledPostBatch, model.batch_id == TableScheduledPostBatch.id)
                .filter(TableScheduledPostBatch.status == "active")
                .group_by(model.status)
                .all()
            )
            counts = {status: count for status, count in rows}
            return {
                "total": sum(counts.values()),
                "scheduled": counts.get("scheduled"),
                "posted": counts.get("posted"),
                "failed": counts.get("failed"),
                "pending": counts.get("pending"),
                "cancelled": counts.get("cancelled"),
            }
        except Exception:
            logger.exception("get_stats failed")
            raise

    def schedule_from_path(self, filepath: str, title: str | None = None) -> dict[str, Any]:
        # Parse an Excel file already on disk, create a batch, and create pending posts linked to it.
        if title is None:
            filename = os.path.basename(filepath)
            title = filename.rsplit(".", 1)[0] if "." in filename else filename

        schedule_batch = ScheduledPostBatchRepository(self.db)
        schedule_post = ScheduledPostRepository(self.db)
        batch = schedule_batch.create_batch({"title": title})

        try:
            parsed = parse_excel(filepath)
        except ValueError as e:
            raise ValueError(str(e))

        created = []
        for post in parsed:
            post["status"] = "pending"
            post["batch_id"] = batch.id
            row = schedule_post.create_scheduled_post(post)
            created.append(schedule_post.to_dict(row))

        schedule_post.save()
        logger.info("Scheduled %d posts from Excel | batch_id=%d file=%s", len(created), batch.id, filepath)
        return {"batch": schedule_batch.to_dict(batch), "count": len(created), "preview": created[:10]}

    async def upload_excel(self, file: UploadFile, title: str | None = None) -> dict[str, Any]:
        # Save an uploaded file to disk, then schedule its posts.
        try:
            FileUploadHandler.validate_file(file)
            content = await file.read()
            if len(content) > FileUploadHandler.MAX_SIZE:
                raise ValueError("File size exceeds 10 MB")
            filename = FileUploadHandler.generate_filename(file.filename)
            filepath = FileUploadHandler.save_to_disk(filename, content)
            logger.info("scheduler_handler.upload_excel | file=%s", filepath)
            if not title:
                title = file.filename.rsplit(".", 1)[0] if "." in file.filename else file.filename
            return self.schedule_from_path(filepath, title=title)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception:
            logger.exception("upload_excel failed")
            raise

    def list_posts(self, status: str | None = None, batch_id: int | None = None) -> list[dict[str, Any]]:
        # List scheduled posts, optionally filtered by status or batch.
        try:
            q = self.db.query(TableScheduledPost)
            if status:
                q = q.filter(TableScheduledPost.status == status)
            if batch_id:
                q = q.filter(TableScheduledPost.batch_id == batch_id)
            q = q.order_by(TableScheduledPost.scheduled_time.asc())
            return rows_to_dicts(q.all())
        except Exception:
            logger.exception("list_posts failed")
            raise

    def get_batch_posts(self, batch_id: int) -> list[dict[str, Any]]:
        return self.list_posts(batch_id=batch_id)

    def _find_post(self, post_id: int, allowed_statuses: set[str]):
        # Find post by id and validate status. Raises ValueError on issues.
        schedule_post= ScheduledPostRepository(self.db)
        post = schedule_post.get_post_for_update(post_id, allowed_statuses)
        if not post:
            raise ValueError(f"No scheduled post with id {post_id}")
        return schedule_post, post


    def cancel_post(self, post_id: int) -> dict[str, Any]:
        # Cancel a pending or scheduled post; revoke the celery task if already dispatched.
        try:
            schedule_post, post = self._find_post(post_id, {"pending", "scheduled"})
            task_id = getattr(post, "task_id", None)
            if task_id:
                try:
                    app.control.revoke(task_id)
                except Exception:
                    logger.exception("revoke failed for task %s", task_id)
            post.status = "cancelled"
            schedule_post.save()
            return {"success": True, "message": f"Cancelled post {post_id}"}
        except ValueError as e:
            return {"error": True, "message": str(e)}
        except Exception:
            logger.exception("cancel_post failed")
            raise

    def get_batches(self) -> list[dict[str, Any]]:
        # Return each upload batch with its post count and status breakdown.
        try:
            return ScheduledPostBatchRepository(self.db).get_batches_with_counts()
        except Exception:
            logger.exception("get_batches failed")
            raise

    def delete_batch(self, batch_id: int) -> dict[str, Any]:
        # Revoke dispatched celery tasks, then hard delete the batch and its posts.
        try:
            posts = (
                self.db.query(TableScheduledPost)
                .filter(TableScheduledPost.batch_id == batch_id)
                .all()
            )
            task_ids = [p.task_id for p in posts if getattr(p, "task_id", None)]
            if task_ids:
                for tid in task_ids:
                    try:
                        app.control.revoke(tid)
                    except Exception:
                        logger.exception("revoke failed for task %s", tid)
            if not ScheduledPostBatchRepository(self.db).delete_batch(batch_id):
                return {"error": True, "message": f"No batch with id {batch_id}"}
            return {"success": True, "revoked": len(task_ids), "message": f"Deleted batch {batch_id}"}
        except Exception:
            logger.exception("delete_batch failed")
            raise

    def schedule_batch(self, batch_id: int) -> dict[str, Any]:
        # Confirm a batch is scheduled. Celery beat dispatches each post at its scheduled_time.
        try:
            batch = ScheduledPostBatchRepository(self.db).get_batch(batch_id)
            if not batch:
                return {"error": True, "message": f"No batch with id {batch_id}"}
            self.db.query(TableScheduledPost).filter(
                TableScheduledPost.batch_id == batch_id,
                TableScheduledPost.status == "pending",
            ).update({"status": "scheduled"})
            self.db.commit()
            return {"batch_id": batch_id, "pending": 0, "status": "scheduled"}
        except Exception:
            logger.exception("schedule_batch failed")
            raise
