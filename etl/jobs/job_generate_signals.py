"""
Job: generate strategy target-weight signals from stored factor values.

Reads z-scored factor values (dwd_factor_value) and adjusted prices, runs each
configured strategy, and upserts dm_strategy_signal.
"""

from __future__ import annotations

import logging
from datetime import date

import pandas as pd  # type: ignore
from sqlalchemy import create_engine, text  # type: ignore

from etl.config import CONTRACTS  # type: ignore
from etl.loaders.db_loader import DbConfig, DbLoader
from etl.strategies.base import StrategyContext
from etl.strategies.registry import build_strategies

logger = logging.getLogger(__name__)


def _load_factors(engine, start_date: date, end_date: date) -> pd.DataFrame:
    return pd.read_sql(
        text(
            "SELECT security_id, trade_date, factor_id, factor_value FROM dwd_factor_value "
            "WHERE value_type = 'zscore' AND trade_date BETWEEN :s AND :e"
        ),
        engine,
        params={"s": start_date, "e": end_date},
    )


def _load_prices(engine, start_date: date, end_date: date) -> pd.DataFrame:
    df = pd.read_sql(
        text("SELECT security_id, trade_date, close, adj_factor FROM ods_daily_bar WHERE trade_date BETWEEN :s AND :e"),
        engine,
        params={"s": start_date, "e": end_date},
    )
    if not df.empty:
        adj = pd.to_numeric(df["adj_factor"], errors="coerce").fillna(1.0)
        df["close_adj"] = pd.to_numeric(df["close"], errors="coerce") * adj
    return df


def run(start_date: date, end_date: date, db_url: str) -> int:
    engine = create_engine(db_url, future=True)
    factors = _load_factors(engine, start_date, end_date)
    prices = _load_prices(engine, start_date, end_date)
    if factors.empty or prices.empty:
        logger.warning("no factor/price data for signal generation")
        return 0

    ctx = StrategyContext(factors=factors, prices=prices)
    loader = DbLoader(DbConfig(url=db_url), table_contracts=CONTRACTS)
    total = 0
    for sid, strategy in build_strategies().items():
        signals = strategy.generate_signals(ctx)
        if signals.empty:
            logger.warning("strategy %s produced no signals", sid)
            continue
        loader.upsert(
            "dm_strategy_signal", signals,
            key_cols=["strategy_id", "security_id", "signal_time", "signal_type"],
        )
        total += len(signals)
        logger.info("strategy %s -> %d signals", sid, len(signals))
    return total
