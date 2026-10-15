"""
Job: sync the security master list (dim_security) from Tushare stock_basic.

Intended to run as a prerequisite for the daily bar job so that ts_code ->
security_id mapping is available.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd  # type: ignore

from etl.config import CONTRACTS  # type: ignore
from etl.extractors.tushare_extractor import TushareConfig, TushareExtractor
from etl.loaders.db_loader import DbConfig, DbLoader


_EXCHANGE_BY_SUFFIX = {"SH": "SSE", "SZ": "SZSE", "BJ": "BSE", "HK": "HKEX"}


def _to_dim_security_df(raw_df: pd.DataFrame) -> pd.DataFrame:
    """
    Map Tushare stock_basic schema to the dim_security contract.

    stock_basic does not provide `exchange`/`security_type` directly, so we
    derive the exchange from the ts_code suffix and treat these rows as equities.
    Missing optional columns are filled with safe defaults.
    """
    if raw_df.empty:
        return raw_df

    df = raw_df.copy()
    df["security_id"] = df["ts_code"]

    def _ensure(col: str, value=None) -> None:
        if col not in df.columns:
            df[col] = value

    _ensure("symbol")
    _ensure("name")
    _ensure("list_date")
    _ensure("delist_date", None)

    if "exchange" not in df.columns:
        df["exchange"] = (
            df["ts_code"].astype(str).str.rsplit(".").str[-1].str.upper().map(_EXCHANGE_BY_SUFFIX)
        )
    df["security_type"] = "stock"

    if "curr_currency" in df.columns:
        df["currency"] = df["curr_currency"].fillna("CNY")
    else:
        df["currency"] = "CNY"
    df["status"] = "listed"
    df["updated_at"] = datetime.now(timezone.utc)

    cols = [
        "security_id",
        "ts_code",
        "symbol",
        "name",
        "exchange",
        "security_type",
        "list_date",
        "delist_date",
        "status",
        "currency",
        "updated_at",
    ]
    return df[cols]  # type: ignore[return-value]


def run(tushare_token: str, db_url: str) -> None:
    """
    Entrypoint for the security master sync job.
    """
    extractor = TushareExtractor(TushareConfig(token=tushare_token))
    raw_df = extractor.get_stock_basic()

    std_df = _to_dim_security_df(raw_df)

    loader = DbLoader(DbConfig(url=db_url), table_contracts=CONTRACTS)
    loader.upsert("dim_security", std_df, key_cols=["security_id"])
