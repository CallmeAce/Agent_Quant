"""
Job: compute the configured factor set and write dwd_factor_value.

Resolves the pilot universe (ts_code -> security_id), loads a FactorContext from
the ODS tables, runs the factor pipeline, and upserts results.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import List

import pandas as pd  # type: ignore
from sqlalchemy import create_engine, text  # type: ignore

from etl.config import CONTRACTS, load_factor_pipeline, load_universe  # type: ignore
from etl.factors.data import load_context
from etl.factors.pipeline import run_factors
from etl.loaders.db_loader import DbConfig, DbLoader

logger = logging.getLogger(__name__)


def _resolve_security_ids(db_url: str, ts_codes: List[str]) -> List[str]:
    engine = create_engine(db_url, future=True)
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT security_id FROM dim_security WHERE ts_code = ANY(:codes)"),
            {"codes": ts_codes},
        ).mappings().all()
    return [r["security_id"] for r in rows]


def run(start_date: date, end_date: date, db_url: str, universe_name: str = "universe_pilot") -> int:
    universe = load_universe(universe_name)
    pipeline_cfg = load_factor_pipeline()

    security_ids = _resolve_security_ids(db_url, universe["ts_codes"])
    if not security_ids:
        logger.warning("no security_ids resolved for universe; ensure dim_security is synced")
        return 0

    ctx = load_context(db_url, security_ids, start_date, end_date, benchmark_index=universe["benchmark_index"])
    result = run_factors(
        ctx,
        pipeline_cfg["factor_ids"],
        zscore=pipeline_cfg["zscore"],
        calc_version=pipeline_cfg["calc_version"],
    )
    if result.empty:
        logger.warning("factor pipeline produced no rows")
        return 0

    loader = DbLoader(DbConfig(url=db_url), table_contracts=CONTRACTS)
    loader.upsert("dwd_factor_value", result, key_cols=["security_id", "trade_date", "factor_id"])
    logger.info("computed %d factor rows for %d securities", len(result), len(security_ids))
    return len(result)
