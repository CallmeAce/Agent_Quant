"""
Job: sync index daily bars (ods_index_daily) for a benchmark index.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from etl.config import CONTRACTS  # type: ignore
from etl.extractors.tushare_extractor import TushareConfig, TushareExtractor
from etl.loaders.db_loader import DbConfig, DbLoader
from etl.transformers.market_transformer import standardize_index_daily


def _batch_id(index_id: str) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"index_daily_{index_id}_{ts}"


def run(index_id: str, start_date: date, end_date: date, tushare_token: str, db_url: str) -> None:
    extractor = TushareExtractor(TushareConfig(token=tushare_token))
    raw_df = extractor.get_index_daily(index_id, start_date, end_date)
    std_df = standardize_index_daily(raw_df, batch_id=_batch_id(index_id), source="tushare")
    loader = DbLoader(DbConfig(url=db_url), table_contracts=CONTRACTS)
    loader.upsert("ods_index_daily", std_df, key_cols=["index_id", "trade_date"])
