"""
Job: sync daily_basic (valuation/liquidity/size) for a universe over a date range.
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
from etl.transformers.market_transformer import standardize_daily_basic

logger = logging.getLogger(__name__)


def _batch_id() -> str:
    return f"daily_basic_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"


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
            raw = extractor.get_daily_basic(code, start_date, end_date)
        except Exception as exc:  # keep going; log and skip this code
            logger.warning("daily_basic failed for %s: %s", code, exc)
            continue
        std = standardize_daily_basic(raw, security_map, batch_id, "tushare")
        std = std[std["security_id"].notna()]
        if not std.empty:
            frames.append(std)
        time.sleep(0.35)

    if frames:
        combined = pd.concat(frames, ignore_index=True)
        loader = DbLoader(DbConfig(url=db_url), table_contracts=CONTRACTS)
        loader.upsert("ods_daily_basic", combined, key_cols=["security_id", "trade_date"])
