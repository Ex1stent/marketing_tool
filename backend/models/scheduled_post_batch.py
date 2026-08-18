from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from models.engine import TableScheduledPostBatch, row_to_dict, set_model_fields
from utils.logger import logger


class ScheduledPostBatchRepository:
    def __init__(self, session: Session):
        self.session = session
        self.model = TableScheduledPostBatch

    def create_batch(self, payload: dict[str, Any]):
        model_obj = self.model()
        set_model_fields(self.session, model_obj, payload)
        return model_obj

    def list_batches(self) -> list[Any]:
        return self.session.query(self.model).filter(self.model.status == 'active').order_by(self.model.created_at.desc()).all()

    def get_batch(self, batch_id: int) -> Any | None:
        return self.session.query(self.model).filter_by(id=batch_id, status='active').first()

    def get_batches_with_counts(self) -> list[dict[str, Any]]:
        # Return all batches with post count and status breakdown.
        from models.engine import TableScheduledPost

        batches = self.list_batches()
        result = []
        for batch in batches:
            posts = self.session.query(TableScheduledPost).filter(TableScheduledPost.batch_id == batch.id).all()
            statuses: dict[str, int] = {}
            for post in posts:
                statuses[post.status] = statuses.get(post.status, 0) + 1
            result.append({
                "id": batch.id,
                "title": batch.title,
                "created_at": self.to_dict(batch)["created_at"],
                "count": len(posts),
                "statuses": statuses,
            })
        return result

    def save(self):
        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            logger.exception("Failed to save scheduled post batch %s", e)

    def delete_batch(self, batch_id: int) -> bool:
        # Soft delete: mark batch inactive and cancel pending posts.
        from models.engine import TableScheduledPost

        row = self.session.query(self.model).filter_by(id=batch_id, status='active').first()
        if not row:
            return False
        row.status = 'inactive'
        row.updated_at = datetime.utcnow()
        self.session.query(TableScheduledPost).filter(
            TableScheduledPost.batch_id == batch_id,
            TableScheduledPost.status == 'pending'
        ).update({"status": "cancelled"})
        self.session.commit()
        return True
       

    def to_dict(self, row: Any) -> dict[str, Any]:
        return row_to_dict(row)
