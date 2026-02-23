"""
Job: load Tushare daily bars into ods_daily_bar.

Intended to be called by the Openclaw Agent with a specific trade_date.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Dict, Iterable

import pandas as pd  # type: ignore

from etl.config import tables as tables_config  # type: ignore
from etl.extractors.tushare_extractor import TushareConfig, TushareExtractor
from etl.loaders.db_loader import DbConfig, DbLoader
from etl.transformers.market_transformer import standardize_daily_bar


def load_security_map() -> Dict[str, str]:
    """
    Placeholder: load ts_code -> security_id mapping from dim_security.
    """
    # Implement DB lookup here; for now we return an empty mapping.
    return {}


def generate_batch_id(trade_date: date) -> str:
    return f"tushare_daily_{trade_date.strftime('%Y%m%d')}_{datetime.utcnow().strftime('%H%M%S')}"


def run(trade_date: date, tushare_token: str, db_url: str) -> None:
    """
    Entrypoint for the daily bar job.
    """
    batch_id = generate_batch_id(trade_date)

    extractor = TushareExtractor(TushareConfig(token=tushare_token))
    raw_df = extractor.get_daily_bar(trade_date)

    security_map = load_security_map()
    std_df = standardize_daily_bar(
        raw_df=raw_df,
        security_map=security_map,
        batch_id=batch_id,
        source="tushare",
    )

    # Basic validation stub: drop rows without security_id
    std_df = std_df[std_df["security_id"].notna()].reset_index(drop=True)

    loader = DbLoader(DbConfig(url=db_url), table_contracts=tables_config.CONTRACTS)
    loader.upsert("ods_daily_bar", std_df, key_cols=["security_id", "trade_date"])

