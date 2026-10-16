"""
Job: sync financial statements (ods_financial_statement) for a universe.

For each security, fetches fina_indicator / income / balancesheet / cashflow and
merges them into the unified contract (statement_type='ALL').
"""

from __future__ import annotations

import logging
import time
from datetime import date, datetime, timezone
from typing import List

import pandas as pd  # type: ignore

from etl.config import CONTRACTS  # type: ignore
from etl.extractors.tushare_extractor import TushareConfig, TushareExtractor
from etl.jobs.job_tushare_daily_bar import load_security_map
from etl.loaders.db_loader import DbConfig, DbLoader
from etl.transformers.financial_transformer import standardize_financials

logger = logging.getLogger(__name__)


def _batch_id() -> str:
    return f"financials_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"


def run(ts_codes: List[str], start_date: date, end_date: date, tushare_token: str, db_url: str) -> None:
    if not ts_codes:
        logger.warning("empty universe; nothing to sync")
        return

    security_map = load_security_map(db_url)
    extractor = TushareExtractor(TushareConfig(token=tushare_token))
    batch_id = _batch_id()

    frames: List[pd.DataFrame] = []
    for code in ts_codes:
        try:
            fina = extractor.get_fina_indicator(code, start_date, end_date)
            income = extractor.get_income(code, start_date, end_date)
            balance = extractor.get_balancesheet(code, start_date, end_date)
            cash = extractor.get_cashflow(code, start_date, end_date)
        except Exception as exc:
            logger.warning("financials failed for %s: %s", code, exc)
            continue
        std = standardize_financials(
            security_map, batch_id, "tushare",
            fina_df=fina, income_df=income, balancesheet_df=balance, cashflow_df=cash,
        )
        if not std.empty:
            frames.append(std)
        time.sleep(0.35)

    if frames:
        combined = pd.concat(frames, ignore_index=True)
        loader = DbLoader(DbConfig(url=db_url), table_contracts=CONTRACTS)
        loader.upsert("ods_financial_statement", combined, key_cols=["security_id", "report_period", "statement_type"])
