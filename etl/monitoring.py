"""
Operational monitoring: record job runs and expose data freshness / job status.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import create_engine, text  # type: ignore


def record_job_run(
    db_url: str,
    job_name: str,
    status: str,
    rows_affected: int = 0,
    duration_seconds: float = 0.0,
    message: str = "",
) -> None:
    engine = create_engine(db_url, future=True)
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO ops_job_run (job_name, run_time, status, duration_seconds, rows_affected, message) "
                "VALUES (:job, :t, :status, :dur, :rows, :msg)"
            ),
            {"job": job_name, "t": datetime.now(timezone.utc), "status": status, "dur": duration_seconds, "rows": rows_affected, "msg": message[:1000]},
        )


def get_data_freshness(db_url: str) -> list:
    engine = create_engine(db_url, future=True)
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT table_name, latest_date, row_count FROM v_data_freshness ORDER BY table_name")).mappings().all()
    return [dict(r) for r in rows]


def get_recent_job_runs(db_url: str, limit: int = 50) -> list:
    engine = create_engine(db_url, future=True)
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT job_name, run_time, status, duration_seconds, rows_affected, message FROM ops_job_run ORDER BY run_time DESC LIMIT :lim"),
            {"lim": limit},
        ).mappings().all()
    return [dict(r) for r in rows]


def get_system_status(db_url: str) -> dict:
    freshness = get_data_freshness(db_url)
    engine = create_engine(db_url, future=True)
    with engine.connect() as conn:
        last = conn.execute(
            text(
                "SELECT DISTINCT ON (job_name) job_name, run_time, status FROM ops_job_run "
                "ORDER BY job_name, run_time DESC"
            )
        ).mappings().all()
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data_freshness": freshness,
        "jobs": [dict(r) for r in last],
    }
