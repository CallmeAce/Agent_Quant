"""Liquidity / size factors (daily_basic + prices)."""

from __future__ import annotations

import numpy as np  # type: ignore
import pandas as pd  # type: ignore

from etl.factors.base import FactorContext, FactorFn, make_output

FACTOR_COLUMNS = ["security_id", "trade_date", "factor_id", "factor_value"]


def _empty() -> pd.DataFrame:
    return pd.DataFrame(columns=FACTOR_COLUMNS)


def _turnover_20d(ctx: FactorContext) -> pd.DataFrame:
    db = ctx.daily_basic
    if db.empty or "turnover_rate" not in db.columns:
        return _empty()
    db = db.copy()
    db["trade_date"] = pd.to_datetime(db["trade_date"])
    db = db.sort_values(["security_id", "trade_date"])
    roll = db.groupby("security_id")["turnover_rate"].transform(
        lambda s: pd.to_numeric(s, errors="coerce").rolling(20, min_periods=20).mean()
    )
    return make_output(db["security_id"], db["trade_date"], "TURNOVER_20D", roll)


def _amount_20d(ctx: FactorContext) -> pd.DataFrame:
    df = ctx.sorted_prices()
    if df.empty or "amount" not in df.columns:
        return _empty()
    roll = df.groupby("security_id")["amount"].transform(
        lambda s: pd.to_numeric(s, errors="coerce").rolling(20, min_periods=20).mean()
    )
    return make_output(df["security_id"], df["trade_date"], "AMOUNT_20D", roll)


def _log_total_mv(ctx: FactorContext) -> pd.DataFrame:
    db = ctx.daily_basic
    if db.empty or "total_mv" not in db.columns:
        return _empty()
    mv = pd.to_numeric(db["total_mv"], errors="coerce")
    val = np.where(mv > 0, np.log(mv), np.nan)
    return make_output(db["security_id"], db["trade_date"], "LOG_TOTAL_MV", val)


def _price_level(ctx: FactorContext) -> pd.DataFrame:
    df = ctx.sorted_prices()
    if df.empty or "close_adj" not in df.columns:
        return _empty()
    px = pd.to_numeric(df["close_adj"], errors="coerce")
    val = np.where(px > 0, np.log(px), np.nan)
    return make_output(df["security_id"], df["trade_date"], "PRICE_LEVEL", val)


def _illiquidity_20d(ctx: FactorContext) -> pd.DataFrame:
    df = ctx.sorted_prices()
    if df.empty or "amount" not in df.columns or "close_adj" not in df.columns:
        return _empty()
    df = df.copy()
    df["ret_abs"] = df.groupby("security_id")["close_adj"].pct_change().abs()
    amount = pd.to_numeric(df["amount"], errors="coerce")
    illiq = np.where((amount.notna()) & (amount > 0), df["ret_abs"] / amount, np.nan)
    df["illiq"] = illiq
    roll = df.groupby("security_id")["illiq"].transform(
        lambda s: s.rolling(20, min_periods=20).mean()
    )
    return make_output(df["security_id"], df["trade_date"], "ILLIQUIDITY_20D", roll)


FACTORS: dict[str, FactorFn] = {
    "TURNOVER_20D": _turnover_20d,
    "AMOUNT_20D": _amount_20d,
    "LOG_TOTAL_MV": _log_total_mv,
    "PRICE_LEVEL": _price_level,
    "ILLIQUIDITY_20D": _illiquidity_20d,
}
