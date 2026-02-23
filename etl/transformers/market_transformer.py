"""
Market data transformers.

Convert raw Tushare/QMT frames into the unified ODS contracts defined in
docs/data_contracts.md and etl/config/tables.yml.
"""

from __future__ import annotations

from datetime import datetime
from typing import Mapping

import pandas as pd  # type: ignore


def standardize_daily_bar(
    raw_df: pd.DataFrame,
    security_map: Mapping[str, str],
    batch_id: str,
    source: str,
) -> pd.DataFrame:
    """
    Map Tushare daily bar schema to ods_daily_bar contract.

    Parameters
    ----------
    raw_df : DataFrame
        Raw Tushare daily bar, including `ts_code`, `trade_date`, price fields.
    security_map : Mapping[str, str]
        ts_code -> security_id mapping from dim_security.
    batch_id : str
        Ingestion batch identifier.
    source : str
        Data source label, e.g. "tushare".
    """
    if raw_df.empty:
        return raw_df

    df = raw_df.copy()
    df["security_id"] = df["ts_code"].map(security_map)
    df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
    df["change"] = df["close"] - df["pre_close"]
    df["pct_change"] = df["change"] / df["pre_close"]
    df["adj_factor"] = df.get("adj_factor", 1.0)
    df["source"] = source
    df["ingest_batch_id"] = batch_id
    df["updated_at"] = datetime.utcnow()

    cols = [
        "security_id",
        "trade_date",
        "open",
        "high",
        "low",
        "close",
        "pre_close",
        "change",
        "pct_change",
        "vol",
        "amount",
        "adj_factor",
        "source",
        "ingest_batch_id",
        "updated_at",
    ]
    return df[cols]

