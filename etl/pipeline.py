"""
Pilot pipeline orchestration: sync -> factors -> signals -> backtest.

Run as a one-shot bootstrap for the pilot universe:
    python -m etl.pipeline --start 2022-01-01 --end 2024-12-31 [--skip-sync]
"""

from __future__ import annotations

import argparse
import logging
import os
from datetime import date

from etl.config import load_strategies, load_universe  # type: ignore
from etl.jobs import (
    job_compute_factors,
    job_generate_signals,
    job_run_backtest,
    job_sync_daily_basic,
    job_sync_daily_bar_range,
    job_sync_financials,
    job_sync_index_daily,
    job_sync_trade_calendar,
)

logger = logging.getLogger(__name__)


def run_pipeline(start: date, end: date, db_url: str, token: str, run_sync: bool = True) -> None:
    universe = load_universe()
    ts_codes = universe["ts_codes"]
    benchmark = universe["benchmark_index"]

    if run_sync:
        logger.info("sync: trade calendar")
        job_sync_trade_calendar.run("SSE", start, end, token, db_url)
        logger.info("sync: benchmark index")
        job_sync_index_daily.run(benchmark, start, end, token, db_url)
        logger.info("sync: daily bars (range)")
        job_sync_daily_bar_range.run(ts_codes, start, end, token, db_url)
        logger.info("sync: daily basic")
        job_sync_daily_basic.run(ts_codes, start, end, token, db_url)
        logger.info("sync: financials")
        job_sync_financials.run(ts_codes, start, end, token, db_url)

    logger.info("compute factors")
    job_compute_factors.run(start, end, db_url)
    logger.info("generate signals")
    job_generate_signals.run(start, end, db_url)
    for sid in load_strategies():
        logger.info("backtest: %s", sid)
        job_run_backtest.run(sid, start, end, db_url, benchmark_index=benchmark)


def main() -> None:
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"),
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    parser = argparse.ArgumentParser(description="Run the pilot factor/backtest pipeline")
    parser.add_argument("--start", required=True, type=lambda s: date.fromisoformat(s))
    parser.add_argument("--end", required=True, type=lambda s: date.fromisoformat(s))
    parser.add_argument("--skip-sync", action="store_true", help="skip Tushare sync (use existing ODS data)")
    args = parser.parse_args()

    db_url = os.environ.get("DATABASE_URL", "")
    token = os.environ.get("TUSHARE_TOKEN", "")
    if not db_url:
        raise SystemExit("DATABASE_URL is required")
    if not args.skip_sync and not token:
        raise SystemExit("TUSHARE_TOKEN is required unless --skip-sync is set")

    run_pipeline(args.start, args.end, db_url, token, run_sync=not args.skip_sync)


if __name__ == "__main__":
    main()
