"""
Market data transformers.

Convert raw Tushare/QMT frames into the unified ODS contracts defined in
docs/data_contracts.md and etl/config/tables.yml.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Mapping, Optional

import numpy as np  # type: ignore
import pandas as pd  # type: ignore

# Unit conventions for ods_daily_bar (see docs/data_contracts.md):
#   vol    -> shares (股)   : Tushare reports lots (手), 1 lot = 100 shares
#   amount -> yuan (元)     : Tushare reports thousands of yuan (千元)
#   pct_change -> fraction  : 0.0123 means +1.23%
VOL_LOT_TO_SHARES = 100
AMOUNT_KYUAN_TO_YUAN = 1000


def standardize_daily_bar(
    raw_df: pd.DataFrame,
    security_map: Mapping[str, str],
    batch_id: str,
    source: str,
    adj_df: Optional[pd.DataFrame] = None,
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
    adj_df : Optional[DataFrame]
        Adj factor frame with `ts_code`, `adj_factor` columns (from
        Tushare adj_factor). Missing factors are stored as NULL, not 1.0.
    """
    if raw_df.empty:
        return raw_df

    df = raw_df.copy()
    df["security_id"] = df["ts_code"].map(security_map)
    df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date

    close = pd.to_numeric(df["close"], errors="coerce")
    pre_close = pd.to_numeric(df["pre_close"], errors="coerce")
    df["change"] = close - pre_close
    df["pct_change"] = np.where(
        pre_close.notna() & (pre_close != 0), df["change"] / pre_close, np.nan
    )

    # Normalize volume/amount to the contract units (shares / yuan).
    df["vol"] = pd.to_numeric(df["vol"], errors="coerce") * VOL_LOT_TO_SHARES
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce") * AMOUNT_KYUAN_TO_YUAN

    # Adj factor comes from a separate Tushare interface; missing -> NULL.
    if adj_df is not None and not adj_df.empty and "adj_factor" in adj_df.columns:
        df = df.merge(adj_df[["ts_code", "adj_factor"]], on="ts_code", how="left")
    else:
        df["adj_factor"] = np.nan

    df["source"] = source
    df["ingest_batch_id"] = batch_id
    df["updated_at"] = datetime.now(timezone.utc)

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
    return df[cols]  # type: ignore[return-value]

