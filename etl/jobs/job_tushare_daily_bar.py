"""
Job: load Tushare daily bars into ods_daily_bar.

Intended to be called by the Openclaw Agent with a specific trade_date.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from typing import Dict, Iterable, Optional

import pandas as pd  # type: ignore
from sqlalchemy import create_engine, text  # type: ignore

from etl.config import CONTRACTS  # type: ignore
from etl.extractors.tushare_extractor import TushareConfig, TushareExtractor
from etl.loaders.db_loader import DbConfig, DbLoader
from etl.transformers.market_transformer import standardize_daily_bar

logger = logging.getLogger(__name__)


def load_security_map(db_url: str) -> Dict[str, str]:
    """
    Load ts_code -> security_id mapping from dim_security.
    """
    engine = create_engine(db_url, future=True)
    query = text(
        "SELECT ts_code, security_id FROM dim_security WHERE ts_code IS NOT NULL"
    )
    with engine.connect() as conn:
        rows = conn.execute(query).mappings().all()
    return {row["ts_code"]: row["security_id"] for row in rows}


def generate_batch_id(trade_date: date) -> str:
    ts = datetime.now(timezone.utc).strftime("%H%M%S")
    return f"tushare_daily_{trade_date.strftime('%Y%m%d')}_{ts}"


def run(trade_date: date, tushare_token: str, db_url: str) -> None:
    """
    Entrypoint for the daily bar job.
    """
    batch_id = generate_batch_id(trade_date)

    extractor = TushareExtractor(TushareConfig(token=tushare_token))
    raw_df = extractor.get_daily_bar(trade_date)

    adj_df: Optional[pd.DataFrame] = None
    try:
        adj_df = extractor.get_adj_factor(trade_date)
    except Exception as e:  # adj fetch must not block the bar load
        logger.warning("adj_factor fetch failed for %s: %s", trade_date, e)

    security_map = load_security_map(db_url)
    std_df = standardize_daily_bar(
        raw_df=raw_df,
        security_map=security_map,
        batch_id=batch_id,
        source="tushare",
        adj_df=adj_df,
    )

    # Basic validation stub: drop rows without security_id
    std_df = std_df[std_df["security_id"].notna()].reset_index(drop=True)

    loader = DbLoader(DbConfig(url=db_url), table_contracts=CONTRACTS)
    loader.upsert("ods_daily_bar", std_df, key_cols=["security_id", "trade_date"])

