"""
Trading calendar transformer.

Maps Tushare trade_cal into the dim_trade_calendar contract.
"""

from __future__ import annotations

import pandas as pd  # type: ignore


def standardize_trade_calendar(raw_df: pd.DataFrame, exchange: str) -> pd.DataFrame:
    """Map Tushare trade_cal to the dim_trade_calendar contract."""
    if raw_df.empty:
        return raw_df

    df = raw_df.copy()
    df["exchange"] = df.get("exchange", exchange)
    df["trade_date"] = pd.to_datetime(df["cal_date"]).dt.date
    df["is_trading_day"] = pd.to_numeric(df["is_open"], errors="coerce").fillna(0).astype(int)
    if "pretrade_date" in df.columns:
        df["previous_trading_date"] = pd.to_datetime(df["pretrade_date"], errors="coerce").dt.date
    else:
        df["previous_trading_date"] = None

    cols = ["exchange", "trade_date", "is_trading_day", "previous_trading_date"]
    return df[cols]  # type: ignore[return-value]
