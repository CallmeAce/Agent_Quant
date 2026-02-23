"""
Account & trade transformers (QMT -> ODS contracts).
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd  # type: ignore


def standardize_positions(raw_df: pd.DataFrame, batch_id: str, source: str) -> pd.DataFrame:
    """
    Map raw QMT positions into ods_position_snapshot contract.

    Expected raw_df columns include:
    - account_id
    - security_id (or pre‑mapped)
    - quantity
    - available_qty
    - avg_cost
    - market_price
    - snapshot_time
    """
    if raw_df.empty:
        return raw_df

    df = raw_df.copy()
    df["market_value"] = df["quantity"] * df["market_price"]
    df["unrealized_pnl"] = df.get("unrealized_pnl", 0.0)
    df["realized_pnl_daily"] = df.get("realized_pnl_daily", 0.0)
    df["source"] = source
    df["ingest_batch_id"] = batch_id
    df["updated_at"] = datetime.utcnow()
    return df[
        [
            "account_id",
            "security_id",
            "snapshot_time",
            "quantity",
            "available_qty",
            "avg_cost",
            "market_price",
            "market_value",
            "unrealized_pnl",
            "realized_pnl_daily",
            "source",
            "ingest_batch_id",
            "updated_at",
        ]
    ]

