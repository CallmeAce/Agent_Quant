"""
Scheduler for Openclaw QuantOps ETL jobs.

Handles:
- Daily ETL job scheduling (T0/T+1)
- Job dependency management
- Health checks and alerts
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from datetime import datetime, date, timedelta, timezone
from typing import Callable, Dict, List, Optional
import traceback

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import create_engine, text  # type: ignore
from telegram.ext import Application

from etl.config import load_strategies, load_universe  # type: ignore
from etl.jobs import (
    job_compute_factors,
    job_generate_signals,
    job_qmt_daily_position,
    job_run_backtest,
    job_sync_daily_basic,
    job_sync_financials,
    job_sync_index_daily,
    job_sync_security,
    job_sync_trade_calendar,
    job_tushare_daily_bar,
)
from etl.monitoring import record_job_run

logger = logging.getLogger(__name__)

# Asia/Shanghai has no DST, so a fixed +08:00 offset is sufficient and avoids
# a hard dependency on a tz database.
CN_TZ = timezone(timedelta(hours=8))


class Job:
    """Represents an ETL job."""

    def __init__(
        self,
        name: str,
        func: Callable,
        schedule: Optional[str] = None,
        cron: Optional[Dict[str, int]] = None,
        dependencies: Optional[List[str]] = None,
        timeout: int = 3600,
        retries: int = 3,
    ):
        self.name = name
        self.func = func
        self.schedule = schedule  # human-readable label, e.g. "daily", "hourly"
        self.cron = cron  # cron kwargs for APScheduler CronTrigger
        self.dependencies = dependencies or []
        self.timeout = timeout
        self.retries = retries
        self.last_run: Optional[datetime] = None
        self.last_status: Optional[str] = None
        self.last_rows: int = 0
        self.last_duration: float = 0.0

    async def run(self) -> bool:
        """Execute the job."""
        logger.info(f"Starting job: {self.name}")
        self.last_run = datetime.now(timezone.utc)
        started = time.monotonic()
        self.last_rows = 0

        try:
            if asyncio.iscoroutinefunction(self.func):
                result = await asyncio.wait_for(self.func(), timeout=self.timeout)
            else:
                result = await asyncio.to_thread(self.func)
            self.last_status = "success"
            self.last_rows = result if isinstance(result, int) else 0
            self.last_duration = time.monotonic() - started
            logger.info(f"Job completed: {self.name}")
            return True
        except asyncio.TimeoutError:
            self.last_status = "timeout"
            self.last_duration = time.monotonic() - started
            logger.error(f"Job timeout: {self.name}")
            return False
        except Exception as e:
            self.last_status = "failed"
            self.last_duration = time.monotonic() - started
            logger.error(f"Job failed: {self.name} - {e}")
            logger.error(traceback.format_exc())
            return False


class Scheduler:
    """ETL Job Scheduler."""

    def __init__(self) -> None:
        self.database_url = os.environ.get("DATABASE_URL", "")
        self.tushare_token = os.environ.get("TUSHARE_TOKEN", "")
        self.telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        self.admin_chat_id = os.environ.get("TELEGRAM_ADMIN_CHAT_ID", "")

        self.jobs: Dict[str, Job] = {}
        self.running = False
        self.bot_app: Optional[Application] = None
        self.apscheduler = AsyncIOScheduler(timezone=CN_TZ)

        self._register_jobs()

    def _register_jobs(self) -> None:
        """Register all ETL jobs."""
        # Security Master Sync Job (prerequisite for daily bar)
        self.jobs["sync_security"] = Job(
            name="sync_security",
            func=self._job_sync_security,
            schedule="daily",
            cron={"hour": 16, "minute": 0},
            timeout=600,
        )

        # T0 Daily Bar Job
        self.jobs["tushare_daily_bar"] = Job(
            name="tushare_daily_bar",
            func=self._job_tushare_daily_bar,
            schedule="daily",
            cron={"hour": 16, "minute": 30},
            dependencies=["sync_security"],
            timeout=1800,
        )

        # QMT Position Job
        self.jobs["qmt_positions"] = Job(
            name="qmt_positions",
            func=self._job_qmt_positions,
            schedule="daily",
            cron={"hour": 17, "minute": 0},
            dependencies=["tushare_daily_bar"],
            timeout=1800,
        )

        # Health Check Job
        self.jobs["health_check"] = Job(
            name="health_check",
            func=self._job_health_check,
            schedule="hourly",
            cron={"minute": 0},
            timeout=300,
        )

        # --- Factor / strategy / backtest pipeline ---
        self.jobs["sync_trade_calendar"] = Job(
            name="sync_trade_calendar",
            func=self._job_sync_trade_calendar,
            schedule="weekly",
            cron={"day_of_week": "mon", "hour": 8, "minute": 0},
            timeout=600,
        )
        self.jobs["sync_index_daily"] = Job(
            name="sync_index_daily",
            func=self._job_sync_index_daily,
            schedule="daily",
            cron={"hour": 16, "minute": 10},
            timeout=600,
        )
        self.jobs["sync_daily_basic"] = Job(
            name="sync_daily_basic",
            func=self._job_sync_daily_basic,
            schedule="daily",
            cron={"hour": 16, "minute": 20},
            dependencies=["sync_security"],
            timeout=3600,
        )
        self.jobs["sync_financials"] = Job(
            name="sync_financials",
            func=self._job_sync_financials,
            schedule="weekly",
            cron={"day_of_week": "sun", "hour": 20, "minute": 0},
            dependencies=["sync_security"],
            timeout=7200,
        )
        self.jobs["compute_factors"] = Job(
            name="compute_factors",
            func=self._job_compute_factors,
            schedule="daily",
            cron={"hour": 17, "minute": 30},
            dependencies=["tushare_daily_bar", "sync_daily_basic"],
            timeout=3600,
        )
        self.jobs["generate_signals"] = Job(
            name="generate_signals",
            func=self._job_generate_signals,
            schedule="daily",
            cron={"hour": 18, "minute": 0},
            dependencies=["compute_factors"],
            timeout=1800,
        )
        self.jobs["run_backtest"] = Job(
            name="run_backtest",
            func=self._job_run_backtest,
            schedule="daily",
            cron={"hour": 18, "minute": 30},
            dependencies=["generate_signals"],
            timeout=3600,
        )

    async def _job_sync_security(self) -> None:
        """Sync dim_security from Tushare stock_basic."""
        logger.info("Syncing security master from Tushare")
        await asyncio.to_thread(
            job_sync_security.run,
            self.tushare_token,
            self.database_url,
        )

    async def _job_tushare_daily_bar(self) -> None:
        """Fetch daily bar data from Tushare."""
        trade_date = date.today()
        logger.info(f"Fetching Tushare daily bar for {trade_date}")
        await asyncio.to_thread(
            job_tushare_daily_bar.run,
            trade_date,
            self.tushare_token,
            self.database_url,
        )

    async def _job_qmt_positions(self) -> None:
        """Fetch position data from QMT."""
        trade_date = date.today()
        account_ids = [a for a in os.environ.get("QMT_ACCOUNT_IDS", "").split(",") if a]
        logger.info(f"Fetching QMT positions for {trade_date}")
        await asyncio.to_thread(
            job_qmt_daily_position.run,
            trade_date,
            account_ids,
            self.database_url,
        )

    def _window(self, days: int) -> tuple:
        end = date.today()
        return end - timedelta(days=days), end

    async def _job_sync_trade_calendar(self) -> None:
        start, end = self._window(400)
        await asyncio.to_thread(
            job_sync_trade_calendar.run, "SSE", start, end, self.tushare_token, self.database_url
        )

    async def _job_sync_index_daily(self) -> None:
        benchmark = load_universe()["benchmark_index"]
        start, end = self._window(400)
        await asyncio.to_thread(
            job_sync_index_daily.run, benchmark, start, end, self.tushare_token, self.database_url
        )

    async def _job_sync_daily_basic(self) -> None:
        ts_codes = load_universe()["ts_codes"]
        start, end = self._window(400)
        await asyncio.to_thread(
            job_sync_daily_basic.run, ts_codes, start, end, self.tushare_token, self.database_url
        )

    async def _job_sync_financials(self) -> None:
        ts_codes = load_universe()["ts_codes"]
        start, end = self._window(1200)
        await asyncio.to_thread(
            job_sync_financials.run, ts_codes, start, end, self.tushare_token, self.database_url
        )

    async def _job_compute_factors(self) -> int:
        start, end = self._window(400)
        return await asyncio.to_thread(job_compute_factors.run, start, end, self.database_url)

    async def _job_generate_signals(self) -> int:
        start, end = self._window(400)
        return await asyncio.to_thread(job_generate_signals.run, start, end, self.database_url)

    async def _job_run_backtest(self) -> int:
        start, end = self._window(400)
        benchmark = load_universe()["benchmark_index"]
        total = 0
        for sid in load_strategies():
            await asyncio.to_thread(
                job_run_backtest.run, sid, start, end, self.database_url, benchmark
            )
            total += 1
        return total

    async def _job_health_check(self) -> None:
        """Run health checks on all systems."""
        logger.info("Running health check...")
        if not self.database_url:
            logger.warning("DATABASE_URL not set; skipping DB health check")
            return

        def _ping_db() -> None:
            engine = create_engine(self.database_url, future=True)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))

        await asyncio.to_thread(_ping_db)
        logger.info("Database health check OK")

    async def run_job(self, job_name: str) -> bool:
        """Run a specific job with retry logic."""
        job = self.jobs.get(job_name)
        if not job:
            logger.error(f"Job not found: {job_name}")
            return False

        # Check dependencies
        for dep in job.dependencies:
            dep_job = self.jobs.get(dep)
            if dep_job and dep_job.last_status != "success":
                logger.warning(f"Dependency not met: {dep}")
                return False

        # Run with retries
        for attempt in range(job.retries):
            success = await job.run()
            self._record_job_run(job)
            if success:
                return True
            logger.warning(f"Retry {attempt + 1}/{job.retries} for job: {job_name}")
            await asyncio.sleep(60 * (attempt + 1))

        return False

    def _record_job_run(self, job: "Job") -> None:
        if not self.database_url:
            return
        try:
            record_job_run(
                self.database_url,
                job.name,
                job.last_status or "unknown",
                rows_affected=job.last_rows,
                duration_seconds=job.last_duration,
            )
        except Exception as exc:  # monitoring must never break the pipeline
            logger.warning("failed to record job run %s: %s", job.name, exc)

    def _schedule_jobs(self) -> None:
        """Register cron triggers for all jobs that define a cron spec."""
        for name, job in self.jobs.items():
            if not job.cron:
                continue
            self.apscheduler.add_job(
                self.run_job,
                CronTrigger(timezone=CN_TZ, **job.cron),
                args=[name],
                id=name,
                replace_existing=True,
                coalesce=True,
                misfire_grace_time=3600,
            )
            logger.info("Scheduled job %s: %s", name, job.cron)

    async def start(self) -> None:
        """Start the scheduler."""
        logger.info("Starting Scheduler...")
        self.running = True

        # Send startup notification
        if self.telegram_token and self.admin_chat_id:
            self.bot_app = Application.builder().token(self.telegram_token).build()
            await self.bot_app.initialize()
            await self.bot_app.bot.send_message(
                chat_id=self.admin_chat_id,
                text="Scheduler started. Daily jobs will run at scheduled times."
            )

        self._schedule_jobs()
        self.apscheduler.start()
        logger.info("Scheduler started; jobs registered.")

        # Block until stopped (APScheduler drives execution on the event loop).
        while self.running:
            await asyncio.sleep(3600)

    async def stop(self) -> None:
        """Stop the scheduler."""
        self.running = False
        if self.apscheduler.running:
            self.apscheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")


async def main():
    scheduler = Scheduler()
    try:
        await scheduler.start()
    except KeyboardInterrupt:
        await scheduler.stop()


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        level=os.environ.get("LOG_LEVEL", "INFO")
    )
    asyncio.run(main())
