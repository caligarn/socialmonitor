"""SQLAlchemy engine and session helpers."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from socialmonitor.config import settings

engine = create_engine(settings.database_url, echo=False)
SessionLocal = sessionmaker(bind=engine)


def get_session() -> Session:
    """Return a new database session."""
    return SessionLocal()


def init_db() -> None:
    """Create all tables that don't exist yet."""
    from socialmonitor.db.models import Base  # noqa: F811

    Base.metadata.create_all(bind=engine)
