"""Quality factors (point-in-time financials)."""

from __future__ import annotations

import numpy as np  # type: ignore
import pandas as pd  # type: ignore

from etl.factors.base import FactorContext, FactorFn, latest_financials_asof, make_output

FACTOR_COLUMNS = ["security_id", "trade_date", "factor_id", "factor_value"]


def _empty() -> pd.DataFrame:
    return pd.DataFrame(columns=FACTOR_COLUMNS)


def _asof(ctx: FactorContext) -> pd.DataFrame:
    return latest_financials_asof(ctx)


def _ratio_or_compute(df, ratio_col, num_col, den_col, factor_id, scale=1.0) -> pd.DataFrame:
    if ratio_col in df.columns and df[ratio_col].notna().any():
        val = pd.to_numeric(df[ratio_col], errors="coerce")
    else:
        num = pd.to_numeric(df.get(num_col), errors="coerce")
        den = pd.to_numeric(df.get(den_col), errors="coerce")
        val = np.where((den.notna()) & (den != 0), num / den * scale, np.nan)
    return make_output(df["security_id"], df["trade_date"], factor_id, val)


def _roe(ctx: FactorContext) -> pd.DataFrame:
    df = _asof(ctx)
    if df.empty:
        return _empty()
    return _ratio_or_compute(df, "roe", "net_profit", "total_equity", "ROE_TTM", 100.0)


def _roa(ctx: FactorContext) -> pd.DataFrame:
    df = _asof(ctx)
    if df.empty:
        return _empty()
    return _ratio_or_compute(df, "roa", "net_profit", "total_assets", "ROA_TTM", 100.0)


def _ratio_direct(df, col, factor_id) -> pd.DataFrame:
    if col not in df.columns:
        return _empty()
    return make_output(df["security_id"], df["trade_date"], factor_id, df[col])


def _gross_margin(ctx: FactorContext) -> pd.DataFrame:
    df = _asof(ctx)
    if df.empty:
        return _empty()
    return _ratio_direct(df, "gross_margin", "GROSS_MARGIN")


def _net_margin(ctx: FactorContext) -> pd.DataFrame:
    df = _asof(ctx)
    if df.empty:
        return _empty()
    return _ratio_direct(df, "net_margin", "NET_MARGIN")


def _debt_to_equity(ctx: FactorContext) -> pd.DataFrame:
    df = _asof(ctx)
    if df.empty:
        return _empty()
    liab = pd.to_numeric(df.get("total_liabilities"), errors="coerce")
    eq = pd.to_numeric(df.get("total_equity"), errors="coerce")
    val = np.where((eq.notna()) & (eq != 0), liab / eq, np.nan)
    return make_output(df["security_id"], df["trade_date"], "DEBT_TO_EQUITY", val)


def _ocf_to_np(ctx: FactorContext) -> pd.DataFrame:
    df = _asof(ctx)
    if df.empty:
        return _empty()
    ocf = pd.to_numeric(df.get("operating_cashflow"), errors="coerce")
    np_ = pd.to_numeric(df.get("net_profit"), errors="coerce")
    val = np.where((np_.notna()) & (np_ != 0), ocf / np_, np.nan)
    return make_output(df["security_id"], df["trade_date"], "OCF_TO_NETPROFIT", val)


FACTORS: dict[str, FactorFn] = {
    "ROE_TTM": _roe,
    "ROA_TTM": _roa,
    "GROSS_MARGIN": _gross_margin,
    "NET_MARGIN": _net_margin,
    "DEBT_TO_EQUITY": _debt_to_equity,
    "OCF_TO_NETPROFIT": _ocf_to_np,
}
