from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from models.engine import TableWebhookEvent, set_model_fields
from utils.logger import logger


def _to_timestamp(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    try:
        raw_value = int(value)
        if raw_value > 10_000_000_000:
            raw_value = raw_value / 1000
        return datetime.fromtimestamp(raw_value, tz=timezone.utc).replace(tzinfo=None)
    except (TypeError, ValueError, OSError):
        return None


class WebhookRepository:
    def __init__(self, session: Session):
        self.session = session
        self.model = TableWebhookEvent

    def add_event(self, payload):
        model_obj = self.model()
        set_model_fields(self.session, model_obj, payload)
        return model_obj

    def save_event(self):
        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            logger.exception("Failed to save webhook event")
        



