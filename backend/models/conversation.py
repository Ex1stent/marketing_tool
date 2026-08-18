from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from models.engine import SessionLocal, TableConversation, row_to_dict, set_model_fields
from utils.logger import logger


class ConversationRepository:
    def __init__(self, session: Session):
        self.session = session
        self.model = TableConversation

    def create(self, payload: dict[str, Any]):
        conversation = self.model()
        set_model_fields(self.session, conversation, payload)
        return conversation

    def list_all(self, page: int = 1, limit: int = 10) -> list[dict[str, Any]]:
        rows = self.session.query(self.model).filter(self.model.status == 'active').order_by(self.model.updated_at.desc()).offset((page - 1) * limit).limit(limit).all()
        return [row_to_dict(r) for r in rows]

    def get_conversation(self, conv_id: int | None = None, title: str | None = None) -> dict[str, Any] | None:
        query = self.session.query(self.model).filter(self.model.status == 'active')
        if conv_id:
            query = query.filter_by(id=conv_id)
        if title:
            query = query.filter_by(title=title)
        row = query.first()
        return row_to_dict(row) if row else None

    def delete(self, conv_id: int) -> bool:
        row = self.session.query(self.model).filter_by(id=conv_id).first()
        if not row:
            return False
        row.status = "inactive"
        row.updated_at = datetime.utcnow()
        # self.save()
        return True

    def update(self, conv_id: int, payload: dict[str, Any]) -> None:
        row = self.session.query(self.model).filter_by(id=conv_id).first()
        if row:
            set_model_fields(self.session, row, payload)
            row.updated_at = datetime.utcnow()

    def search(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        q = self.session.query(self.model).filter(self.model.status == 'active')
        if query.isdigit():
            q = q.filter(self.model.title.ilike(f'%{query}%') | (self.model.id == int(query)))
        else:
            q = q.filter(self.model.title.ilike(f'%{query}%'))
        return [row_to_dict(r) for r in q.order_by(self.model.updated_at.desc()).limit(limit)]

    def save(self):
        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            logger.exception("Failed to save conversation %s", e)
            
