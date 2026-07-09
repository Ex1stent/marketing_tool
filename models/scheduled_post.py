from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from models.base import Base


class ScheduledPost(Base):
    __tablename__ = "scheduled_posts"
    __table_args__ = {"schema": "meta"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_type = Column(String(50), nullable=False)
    platform = Column(String(50), nullable=False)
    media_url = Column(Text, nullable=True)
    message = Column(Text, nullable=True)
    topic = Column(Text, nullable=True)
    recipient_id = Column(Text, nullable=True)
    location_id = Column(Text, nullable=True)
    scheduled_time = Column(DateTime(timezone=False), nullable=False)
    status = Column(String(50), default="pending")
    task_id = Column(String(255), nullable=True)
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=False), server_default=func.now())
    updated_at = Column(DateTime(timezone=False), server_default=func.now(), onupdate=func.now())

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "post_type": self.post_type,
            "platform": self.platform,
            "media_url": self.media_url,
            "message": self.message,
            "topic": self.topic,
            "recipient_id": self.recipient_id,
            "location_id": self.location_id,
            "scheduled_time": self.scheduled_time.isoformat() if self.scheduled_time else None,
            "status": self.status,
            "task_id": self.task_id,
            "result": self.result,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
