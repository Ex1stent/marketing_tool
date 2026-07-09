from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker

from config import DATABASE_URL
from utils.logger import get_logger

logger = get_logger(__name__)

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=10,
    pool_recycle=1800,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine)

metadata = MetaData(schema="meta")
Base = automap_base(metadata=metadata)

Base.prepare(autoload_with=engine)
logger.info("Database engine ready | url=%s schema=meta", DATABASE_URL)


def prepare_models() -> None:
    from models.scheduled_post import ScheduledPost
    Base.prepare(autoload_with=engine)
    ScheduledPost.__table__.create(engine, checkfirst=True)
    logger.info("ScheduledPost table ensured")
