"""
Factor engine base: shared context, point-in-time financial access, and
cross-sectional transforms.

A factor is a callable: (FactorContext) -> DataFrame[security_id, trade_date,
factor_id, factor_value]. Factors read only from the context so they are pure
and unit-testable with synthetic data.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

import numpy as np  # type: ignore
import pandas as pd  # type: ignore

FACTOR_COLUMNS = ["security_id", "trade_date", "factor_id", "factor_value"]


@dataclass
class FactorContext:
    prices: pd.DataFrame  # security_id, trade_date, close_adj, vol, amount
    daily_basic: pd.DataFrame  # security_id, trade_date, pe_ttm, pb, ps_ttm, dv_ttm, turnover_rate, total_mv, circ_mv, volume_ratio
    financials: pd.DataFrame  # security_id, report_period, announce_date, ratios/absolutes
    index_close: Optional[pd.DataFrame] = None  # trade_date, close (benchmark)

    def sorted_prices(self) -> pd.DataFrame:
        df = self.prices.copy()
        df["trade_date"] = pd.to_datetime(df["trade_date"])
        return df.sort_values(["security_id", "trade_date"])


FactorFn = Callable[[FactorContext], pd.DataFrame]


def make_output(security_id: pd.Series, trade_date: pd.Series, factor_id: str, value) -> pd.DataFrame:
    out = pd.DataFrame(
        {
            "security_id": security_id,
            "trade_date": pd.to_datetime(trade_date).dt.date,
            "factor_id": factor_id,
            "factor_value": pd.to_numeric(value, errors="coerce"),
        }
    )
    out = out.dropna(subset=["factor_value"])
    return out[FACTOR_COLUMNS]


def latest_financials_asof(ctx: FactorContext) -> pd.DataFrame:
    """
    For each (security_id, trade_date) in prices, attach the most recent
    financial record whose announce_date <= trade_date (point-in-time safe).
    """
    fin = ctx.financials.copy()
    if fin.empty:
        return pd.DataFrame()
    fin["announce_date"] = pd.to_datetime(fin["announce_date"], errors="coerce")
    fin = fin.dropna(subset=["announce_date"]).sort_values("announce_date")

    left = ctx.prices[["security_id", "trade_date"]].copy()
    left["trade_date"] = pd.to_datetime(left["trade_date"])
    left = left.sort_values("trade_date")

    merged = pd.merge_asof(
        left,
        fin,
        left_on="trade_date",
        right_on="announce_date",
        by="security_id",
        direction="backward",
    )
    return merged


def winsorize_zscore(values: pd.Series) -> pd.Series:
    """Cross-sectional winsorize (MAD-based) then z-score. NaN-safe."""
    v = pd.to_numeric(values, errors="coerce")
    med = v.median()
    mad = (v - med).abs().median()
    if not np.isfinite(mad) or mad == 0:
        std = v.std()
        if not np.isfinite(std) or std == 0:
            return pd.Series(0.0, index=v.index)
        return ((v - med) / std).clip(-3, 3).fillna(0.0)
    lower, upper = med - 3 * 1.4826 * mad, med + 3 * 1.4826 * mad
    clipped = v.clip(lower, upper)
    std = clipped.std()
    if not np.isfinite(std) or std == 0:
        return pd.Series(0.0, index=v.index)
    return ((clipped - clipped.mean()) / std).fillna(0.0)


def cross_sectional_zscore(ctx: FactorContext, factor_df: pd.DataFrame) -> pd.DataFrame:
    """Apply per-trade_date winsorized z-score to a factor output frame."""
    out = factor_df.copy()
    out["factor_value"] = out.groupby("trade_date")["factor_value"].transform(winsorize_zscore)
    return out
