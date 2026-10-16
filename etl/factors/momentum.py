"""Momentum factors (adjusted prices / volume)."""

from __future__ import annotations

import numpy as np  # type: ignore
import pandas as pd  # type: ignore

from etl.factors.base import FactorContext, FactorFn, make_output

FACTOR_COLUMNS = ["security_id", "trade_date", "factor_id", "factor_value"]


def _empty() -> pd.DataFrame:
    return pd.DataFrame(columns=FACTOR_COLUMNS)


def _price_momentum(ctx: FactorContext, n: int, factor_id: str) -> pd.DataFrame:
    df = ctx.sorted_prices()
    if df.empty or "close_adj" not in df.columns:
        return _empty()
    g = df.groupby("security_id")["close_adj"]
    prev = g.transform(lambda s: s.shift(n))
    val = np.where((prev.notna()) & (prev != 0), df["close_adj"] / prev - 1.0, np.nan)
    return make_output(df["security_id"], df["trade_date"], factor_id, val)


def _vol_momentum(ctx: FactorContext) -> pd.DataFrame:
    df = ctx.sorted_prices()
    if df.empty or "vol" not in df.columns:
        return _empty()
    df = df.copy()
    df["vol"] = pd.to_numeric(df["vol"], errors="coerce")
    grp = df.groupby("security_id")["vol"]
    recent = grp.transform(lambda s: s.rolling(20, min_periods=20).mean())
    prior = grp.transform(lambda s: s.shift(20).rolling(20, min_periods=20).mean())
    val = np.where((prior.notna()) & (prior != 0), recent / prior, np.nan)
    return make_output(df["security_id"], df["trade_date"], "VOL_MOM_20D", val)


FACTORS: dict[str, FactorFn] = {
    "MOM_20D": lambda ctx: _price_momentum(ctx, 20, "MOM_20D"),
    "MOM_60D": lambda ctx: _price_momentum(ctx, 60, "MOM_60D"),
    "MOM_120D": lambda ctx: _price_momentum(ctx, 120, "MOM_120D"),
    "VOL_MOM_20D": _vol_momentum,
}
