from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from models.engine import SessionLocal, TableMessage, set_model_fields, rows_to_dicts
from utils.logger import logger


class MessagesRepository:
    def __init__(self,session: Session):
        self.session = session
        self.model = TableMessage

    def list_messages(self, conv_id: int, page: int = 1, limit: int = 0) -> list[dict[str, Any]]:
        q = self.session.query(self.model).filter_by(conversation_id=conv_id).order_by(self.model.created_at.desc(), self.model.id.desc())
        if limit > 0:
            q = q.offset((page - 1) * limit).limit(limit)
        return list(reversed(rows_to_dicts(q.all())))

    def create_message(self, conv_id: int, role: str, content: str, message_type: str = "text"):
        message = self.model()
        set_model_fields(self.session, message, {"conversation_id": conv_id, "role": role, "content": content, "message_type": message_type})
        return message

    def save(self):
        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            logger.exception("Failed to save messages: %s", e)
