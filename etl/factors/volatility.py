"""Volatility / risk factors (adjusted prices, benchmark for beta)."""

from __future__ import annotations

import numpy as np  # type: ignore
import pandas as pd  # type: ignore

from etl.factors.base import FactorContext, FactorFn, make_output

FACTOR_COLUMNS = ["security_id", "trade_date", "factor_id", "factor_value"]
TRADING_DAYS = 252


def _empty() -> pd.DataFrame:
    return pd.DataFrame(columns=FACTOR_COLUMNS)


def _returns(ctx: FactorContext) -> pd.DataFrame:
    df = ctx.sorted_prices()
    if df.empty or "close_adj" not in df.columns:
        return pd.DataFrame()
    df = df.copy()
    df["ret"] = df.groupby("security_id")["close_adj"].pct_change()
    return df


def _volatility(ctx: FactorContext, n: int, factor_id: str) -> pd.DataFrame:
    df = _returns(ctx)
    if df.empty:
        return _empty()
    roll = df.groupby("security_id")["ret"].transform(lambda s: s.rolling(n, min_periods=n).std())
    val = roll * np.sqrt(TRADING_DAYS)
    return make_output(df["security_id"], df["trade_date"], factor_id, val)


def _max_drawdown(ctx: FactorContext) -> pd.DataFrame:
    df = ctx.sorted_prices()
    if df.empty or "close_adj" not in df.columns:
        return _empty()
    df = df.copy()
    grp = df.groupby("security_id")["close_adj"]
    peak = grp.transform(lambda s: s.cummax())
    dd = np.where((peak.notna()) & (peak > 0), (peak - df["close_adj"]) / peak, np.nan)
    df["dd"] = dd
    roll = df.groupby("security_id")["dd"].transform(lambda s: s.rolling(120, min_periods=120).max())
    return make_output(df["security_id"], df["trade_date"], "MAX_DRAWDOWN_120D", roll)


def _beta(ctx: FactorContext) -> pd.DataFrame:
    df = _returns(ctx)
    if df.empty or ctx.index_close is None or ctx.index_close.empty:
        return _empty()
    idx = ctx.index_close.copy()
    idx["trade_date"] = pd.to_datetime(idx["trade_date"])
    idx = idx.sort_values("trade_date")
    idx["idx_ret"] = pd.to_numeric(idx["close"], errors="coerce").pct_change()
    df = df.merge(idx[["trade_date", "idx_ret"]], on="trade_date", how="left")

    def _roll_cov(s: pd.Series, other: pd.Series, n: int) -> pd.Series:
        prod = (s * other).rolling(n, min_periods=n).mean()
        return prod - s.rolling(n, min_periods=n).mean() * other.rolling(n, min_periods=n).mean()

    def _beta_group(g: pd.DataFrame) -> pd.DataFrame:
        cov = _roll_cov(g["ret"], g["idx_ret"], 120)
        var = _roll_cov(g["idx_ret"], g["idx_ret"], 120)
        g = g.copy()
        g["beta"] = np.where((var.notna()) & (var != 0), cov / var, np.nan)
        return g

    out = df.groupby("security_id", group_keys=False)[df.columns].apply(_beta_group)
    return make_output(out["security_id"], out["trade_date"], "BETA_120D", out["beta"])


FACTORS: dict[str, FactorFn] = {
    "VOLATILITY_20D": lambda ctx: _volatility(ctx, 20, "VOLATILITY_20D"),
    "VOLATILITY_120D": lambda ctx: _volatility(ctx, 120, "VOLATILITY_120D"),
    "MAX_DRAWDOWN_120D": _max_drawdown,
    "BETA_120D": _beta,
}
