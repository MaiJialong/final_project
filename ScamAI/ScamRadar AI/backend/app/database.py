"""SQLAlchemy engine, session factory, and Base metadata."""
from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import get_settings


class Base(DeclarativeBase):
    pass


_settings = get_settings()

# pool_pre_ping avoids stale connections; future=True uses 2.0 semantics.
engine = create_engine(_settings.database_url, pool_pre_ping=True, future=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session() -> Iterator[Session]:
    """FastAPI dependency yielding a scoped DB session."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """Create tables from ORM metadata.

    For production prefer applying db/schema.sql (it sets up the pgvector
    extension and ivfflat indexes). This helper is convenient for tests
    against a throwaway database.
    """
    from . import models  # noqa: F401  (register mappers)

    Base.metadata.create_all(engine)
