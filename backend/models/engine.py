from __future__ import annotations

from typing import Any, Generator
from datetime import timezone
from config import DATABASE_URL
from sqlalchemy import MetaData, create_engine, Column,Integer
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session, sessionmaker
from utils.logger import logger


engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=10,
    pool_recycle=1800,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

metadata = MetaData(schema="marketing_tool")
Base = automap_base(metadata=metadata)


class TableScheduledPost(Base):
    __tablename__ = "scheduled_posts"
    __table_args__ = {"schema":"marketing_tool","extend_existing": "true"}
    id=Column(Integer,primary_key=True)

class TableScheduledPostBatch(Base):
    __tablename__ = "scheduled_post_batches"
    __table_args__ = {"schema":"marketing_tool","extend_existing": "true"}
    id=Column(Integer,primary_key=True)

class TableWebhookEvent(Base):
    __tablename__ = "webhook_events"
    __table_args__ = {"schema":"marketing_tool","extend_existing": "true"}
    id=Column(Integer,primary_key=True)

class TableConversation(Base):
    __tablename__ = "conversations"
    __table_args__ = {"schema":"marketing_tool","extend_existing": "true"}
    id=Column(Integer,primary_key=True)

class TableMessage(Base):
    __tablename__ = "messages"
    __table_args__ = {"schema":"marketing_tool","extend_existing": "true"}
    id=Column(Integer,primary_key=True)

class TableDocumentMetadata(Base):
    __tablename__ = "document_metadata"
    __table_args__ = {"schema":"marketing_tool","extend_existing": "true"}
    id=Column(Integer,primary_key=True)


Base.prepare(autoload_with=engine, reflect=True)
logger.info("Database engine ready | url=%s schema=meta", DATABASE_URL)


def set_model_fields(session: Session, model_obj: Any, payload: dict[str, Any], skip_fields: set[str] | None = None) -> Any:
    for key, value in payload.items():
        if skip_fields and key in skip_fields:
            continue
        if hasattr(model_obj, key):
            setattr(model_obj, key, value)
    session.add(model_obj)
    session.flush()
    return model_obj


def row_to_dict(row: Any) -> dict[str, Any]:
    result = {}
    for column in row.__table__.columns:
        value = getattr(row, column.name)
        if value is not None and hasattr(value, "isoformat"):
            if getattr(value, "tzinfo", None) is None:
                value = value.replace(tzinfo=timezone.utc)
            value = value.isoformat()
        result[column.name] = value
    return result


def rows_to_dicts(rows: list[Any]) -> list[dict[str, Any]]:
    return [row_to_dict(row) for row in rows]
