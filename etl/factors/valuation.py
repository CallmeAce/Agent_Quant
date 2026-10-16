"""Valuation factors (from ods_daily_basic, point-in-time daily)."""

from __future__ import annotations

import numpy as np  # type: ignore
import pandas as pd  # type: ignore

from etl.factors.base import FactorContext, FactorFn, latest_financials_asof, make_output


def _empty() -> pd.DataFrame:
    return pd.DataFrame(columns=["security_id", "trade_date", "factor_id", "factor_value"])


def _direct(ctx: FactorContext, col: str, factor_id: str) -> pd.DataFrame:
    df = ctx.daily_basic
    if df.empty or col not in df.columns:
        return _empty()
    return make_output(df["security_id"], df["trade_date"], factor_id, df[col])


def _reciprocal(ctx: FactorContext, col: str, factor_id: str) -> pd.DataFrame:
    df = ctx.daily_basic
    if df.empty or col not in df.columns:
        return _empty()
    base = pd.to_numeric(df[col], errors="coerce")
    val = np.where(base > 0, 1.0 / base, np.nan)
    return make_output(df["security_id"], df["trade_date"], factor_id, val)


def _pe_ttm(ctx: FactorContext) -> pd.DataFrame:
    return _direct(ctx, "pe_ttm", "PE_TTM")


def _pb(ctx: FactorContext) -> pd.DataFrame:
    return _direct(ctx, "pb", "PB")


def _ps_ttm(ctx: FactorContext) -> pd.DataFrame:
    return _direct(ctx, "ps_ttm", "PS_TTM")


def _dividend_yield(ctx: FactorContext) -> pd.DataFrame:
    return _direct(ctx, "dv_ttm", "DIVIDEND_YIELD_TTM")


def _earnings_yield(ctx: FactorContext) -> pd.DataFrame:
    return _reciprocal(ctx, "pe_ttm", "EARNINGS_YIELD")


def _book_yield(ctx: FactorContext) -> pd.DataFrame:
    return _reciprocal(ctx, "pb", "BOOK_YIELD")


def _peg(ctx: FactorContext) -> pd.DataFrame:
    db = ctx.daily_basic
    if db.empty or "pe_ttm" not in db.columns:
        return _empty()
    fin = latest_financials_asof(ctx)
    if fin.empty or "net_profit_yoy" not in fin.columns:
        return _empty()
    merged = db.merge(
        fin[["security_id", "trade_date", "net_profit_yoy"]],
        on=["security_id", "trade_date"],
        how="left",
    )
    pe = pd.to_numeric(merged["pe_ttm"], errors="coerce")
    g = pd.to_numeric(merged["net_profit_yoy"], errors="coerce")
    val = np.where((g > 0) & (pe > 0), pe / g, np.nan)
    return make_output(merged["security_id"], merged["trade_date"], "PEG", val)


FACTORS: dict[str, FactorFn] = {
    "PE_TTM": _pe_ttm,
    "PB": _pb,
    "PS_TTM": _ps_ttm,
    "DIVIDEND_YIELD_TTM": _dividend_yield,
    "EARNINGS_YIELD": _earnings_yield,
    "BOOK_YIELD": _book_yield,
    "PEG": _peg,
}
