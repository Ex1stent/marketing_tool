from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from models.engine import SessionLocal, TableDocumentMetadata, set_model_fields, row_to_dict
from utils.logger import logger


class DocMetadataRepository:
    def __init__(self,session: Session):
        self.session = session
        self.model = TableDocumentMetadata

    def get_metadata(self, message_ids: list[int]) -> dict[int, dict[str, Any]]:
        rows = self.session.query(self.model).filter(self.model.message_id.in_(message_ids)).all()
        return {r.message_id: row_to_dict(r) for r in rows}

    def add_metadata(self, message_id: int, **kwargs):
        metadata = self.model()
        set_model_fields(self.session, metadata, {"message_id": message_id, **kwargs})
        return metadata

    def save(self):
        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            logger.exception("Failed to save doc metadata: %s", e)
