"""
Job: run a backtest for a strategy and persist run/metrics/NAV/positions.
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime, timezone

import pandas as pd  # type: ignore
from sqlalchemy import create_engine, text  # type: ignore

from etl.backtest.engine import run_backtest
from etl.config import CONTRACTS  # type: ignore
from etl.loaders.db_loader import DbConfig, DbLoader

logger = logging.getLogger(__name__)


def _load_signals(engine, strategy_id: str, start_date: date, end_date: date) -> pd.DataFrame:
    return pd.read_sql(
        text(
            "SELECT strategy_id, security_id, signal_time, target_weight FROM dm_strategy_signal "
            "WHERE strategy_id = :sid AND signal_type = 'TARGET_WEIGHT' AND signal_time BETWEEN :s AND :e"
        ),
        engine,
        params={"sid": strategy_id, "s": start_date, "e": end_date},
    )


def _load_prices(engine, securities, start_date: date, end_date: date) -> pd.DataFrame:
    df = pd.read_sql(
        text("SELECT security_id, trade_date, close, adj_factor FROM ods_daily_bar WHERE trade_date BETWEEN :s AND :e"),
        engine,
        params={"s": start_date, "e": end_date},
    )
    if not df.empty and securities:
        df = df[df["security_id"].isin(securities)]
        adj = pd.to_numeric(df["adj_factor"], errors="coerce").fillna(1.0)
        df["close_adj"] = pd.to_numeric(df["close"], errors="coerce") * adj
    return df


def _load_benchmark(engine, index_id: str, start_date: date, end_date: date) -> pd.DataFrame:
    return pd.read_sql(
        text("SELECT trade_date, close FROM ods_index_daily WHERE index_id = :i AND trade_date BETWEEN :s AND :e ORDER BY trade_date"),
        engine,
        params={"i": index_id, "s": start_date, "e": end_date},
    )


def run(strategy_id: str, start_date: date, end_date: date, db_url: str, benchmark_index: str = "000300.SH", cost_bps: float = 20.0) -> str:
    engine = create_engine(db_url, future=True)
    signals = _load_signals(engine, strategy_id, start_date, end_date)
    if signals.empty:
        logger.warning("no signals for strategy %s in range", strategy_id)
        return ""

    securities = sorted(set(signals["security_id"]))
    prices = _load_prices(engine, securities, start_date, end_date)
    benchmark = _load_benchmark(engine, benchmark_index, start_date, end_date)

    result = run_backtest(signals, prices, benchmark=benchmark, cost_bps=cost_bps)
    if result["nav"].empty:
        logger.warning("backtest produced no NAV for strategy %s", strategy_id)
        return ""

    run_id = f"{strategy_id}_{start_date}_{end_date}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    now = datetime.now(timezone.utc)
    loader = DbLoader(DbConfig(url=db_url), table_contracts=CONTRACTS)

    run_row = pd.DataFrame([{
        "run_id": run_id, "strategy_id": strategy_id, "start_date": start_date, "end_date": end_date,
        "benchmark_index": benchmark_index, "cost_bps": cost_bps,
        "params": json.dumps({"cost_bps": cost_bps, "n_signals": int(len(signals))}),
        "created_at": now,
    }])
    metrics = dict(result["metrics"])
    metrics_row = pd.DataFrame([{"run_id": run_id, **metrics, "created_at": now}])
    nav = result["nav"].copy()
    nav["run_id"] = run_id
    pos = result["positions"].copy()
    if not pos.empty:
        pos["run_id"] = run_id

    loader.upsert("dwd_backtest_run", run_row, key_cols=["run_id"])
    loader.upsert("dwd_backtest_metrics", metrics_row, key_cols=["run_id"])
    loader.upsert("dwd_strategy_nav", nav[["run_id", "trade_date", "nav", "benchmark_nav"]], key_cols=["run_id", "trade_date"])
    if not pos.empty:
        loader.upsert("dwd_strategy_position", pos[["run_id", "security_id", "trade_date", "weight"]], key_cols=["run_id", "security_id", "trade_date"])

    logger.info("backtest %s: total_return=%.4f sharpe=%.2f max_dd=%.4f", run_id, metrics["total_return"], metrics["sharpe"], metrics["max_drawdown"])
    return run_id
