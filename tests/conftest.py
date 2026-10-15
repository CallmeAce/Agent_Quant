"""
Shared pytest fixtures.

DB-backed tests are skipped unless a reachable Postgres is provided via the
TEST_DATABASE_URL (or DATABASE_URL) environment variable, so the core suite
runs without any external service.
"""

from __future__ import annotations

import os

import pytest


@pytest.fixture(scope="session")
def db_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not url:
        pytest.skip("no TEST_DATABASE_URL/DATABASE_URL set; skipping DB tests")
    return url


@pytest.fixture(scope="session")
def live_db(db_url: str):
    """Yield the db_url only if a connection can actually be established."""
    from sqlalchemy import create_engine, text

    try:
        engine = create_engine(db_url, future=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover - environment dependent
        pytest.skip(f"database not reachable: {exc}")
    return db_url
