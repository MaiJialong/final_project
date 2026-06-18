"""Pytest configuration and fixtures.

Forces offline mode so no network/API key is needed. Provides database
fixtures that run the full pipeline against a real Postgres + pgvector
instance when one is reachable, and skip cleanly when it is not (so the
schema/safety unit tests still run anywhere).
"""
import os

# Must be set before any `app.*` import so config/engine pick them up.
os.environ.setdefault("OFFLINE_MODE", "1")
os.environ.setdefault("MINIMAX_API_KEY", "test-key")
# Point tests at a throwaway DB; override with TEST_DATABASE_URL / DATABASE_URL.
os.environ.setdefault(
    "DATABASE_URL",
    os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql+psycopg://scamradar:scamradar@localhost:5432/scamradar",
    ),
)

import pytest
from sqlalchemy import text


@pytest.fixture(scope="session")
def engine():
    """Session-scoped engine bound to a Postgres+pgvector test database.

    Skips every dependent test if the database cannot be reached, so the
    suite still passes in environments without Postgres.
    """
    from sqlalchemy.exc import OperationalError

    from app.database import Base, engine as app_engine
    from app import models  # noqa: F401  (register mappers)

    try:
        with app_engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    except OperationalError as exc:  # pragma: no cover - env dependent
        pytest.skip(f"Postgres/pgvector not available: {exc}")

    Base.metadata.create_all(app_engine)
    yield app_engine
    app_engine.dispose()


@pytest.fixture()
def db_session(engine):
    """Function-scoped session with a clean set of tables per test."""
    from app.database import Base, SessionLocal

    table_names = ", ".join(t.name for t in reversed(Base.metadata.sorted_tables))
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {table_names} RESTART IDENTITY CASCADE"))

    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture()
def client(db_session):
    """FastAPI TestClient wired to the test session."""
    from fastapi.testclient import TestClient

    from app.database import get_session
    from app.main import app

    def _override():
        try:
            yield db_session
            db_session.commit()
        except Exception:
            db_session.rollback()
            raise

    app.dependency_overrides[get_session] = _override
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.clear()
