"""
Job: sync the trading calendar (dim_trade_calendar) from Tushare trade_cal.
"""

from __future__ import annotations

from datetime import date

from etl.config import CONTRACTS  # type: ignore
from etl.extractors.tushare_extractor import TushareConfig, TushareExtractor
from etl.loaders.db_loader import DbConfig, DbLoader
from etl.transformers.calendar_transformer import standardize_trade_calendar


def run(exchange: str, start_date: date, end_date: date, tushare_token: str, db_url: str) -> None:
    extractor = TushareExtractor(TushareConfig(token=tushare_token))
    raw_df = extractor.get_trade_cal(exchange, start_date, end_date)
    std_df = standardize_trade_calendar(raw_df, exchange)
    loader = DbLoader(DbConfig(url=db_url), table_contracts=CONTRACTS)
    loader.upsert("dim_trade_calendar", std_df, key_cols=["exchange", "trade_date"])
