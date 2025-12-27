"""Database connection and session management."""

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from typing import Generator
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Create SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    pool_pre_ping=True,
    poolclass=NullPool if settings.DEBUG else None
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Enable TimescaleDB extension
@event.listens_for(engine, "connect")
def enable_timescaledb(dbapi_conn, connection_record):
    """Enable TimescaleDB extension on database connection."""
    cursor = dbapi_conn.cursor()
    try:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;")
        dbapi_conn.commit()
        logger.info("TimescaleDB extension enabled")
    except Exception as e:
        logger.warning(f"Could not enable TimescaleDB: {e}")
    finally:
        cursor.close()
