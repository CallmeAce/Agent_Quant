import asyncio

from sqlalchemy import create_engine, text

from etl.monitoring import record_job_run
from etl.scheduler import Job, Scheduler


def test_registers_pipeline_jobs():
    sched = Scheduler()
    expected = {
        "sync_security", "tushare_daily_bar", "sync_trade_calendar", "sync_index_daily",
        "sync_daily_basic", "sync_financials", "compute_factors", "generate_signals", "run_backtest",
    }
    assert expected <= set(sched.jobs)
    # dependency wiring
    assert "compute_factors" in sched.jobs["generate_signals"].dependencies
    assert "generate_signals" in sched.jobs["run_backtest"].dependencies


def test_job_run_captures_rows_and_status():
    job = Job(name="dummy", func=lambda: 42)
    ok = asyncio.run(job.run())
    assert ok is True
    assert job.last_status == "success"
    assert job.last_rows == 42


def test_job_run_failure_records_failed():
    def boom():
        raise RuntimeError("boom")
    job = Job(name="dummy_fail", func=boom)
    ok = asyncio.run(job.run())
    assert ok is False
    assert job.last_status == "failed"


def test_record_job_run_persists(live_db):
    record_job_run(live_db, "__test_sched_job__", "success", rows_affected=7, duration_seconds=1.5)
    engine = create_engine(live_db, future=True)
    with engine.begin() as conn:
        rows = conn.execute(text("SELECT status, rows_affected FROM ops_job_run WHERE job_name=:j"), {"j": "__test_sched_job__"}).mappings().all()
        conn.execute(text("DELETE FROM ops_job_run WHERE job_name=:j"), {"j": "__test_sched_job__"})
    assert rows and rows[0]["status"] == "success" and rows[0]["rows_affected"] == 7
