"""Growth factors (point-in-time financials)."""

from __future__ import annotations

from dataclasses import replace

import numpy as np  # type: ignore
import pandas as pd  # type: ignore

from etl.factors.base import FactorContext, FactorFn, latest_financials_asof, make_output

FACTOR_COLUMNS = ["security_id", "trade_date", "factor_id", "factor_value"]
QUARTERS_3Y = 12


def _empty() -> pd.DataFrame:
    return pd.DataFrame(columns=FACTOR_COLUMNS)


def _direct_yoy(ctx: FactorContext, col: str, factor_id: str) -> pd.DataFrame:
    df = latest_financials_asof(ctx)
    if df.empty or col not in df.columns:
        return _empty()
    return make_output(df["security_id"], df["trade_date"], factor_id, df[col])


def _cagr_asof(ctx: FactorContext, value_col: str, factor_id: str) -> pd.DataFrame:
    fin = ctx.financials.copy()
    if fin.empty or value_col not in fin.columns:
        return _empty()
    fin["report_period"] = pd.to_datetime(fin["report_period"], errors="coerce")
    fin = fin.dropna(subset=["report_period"]).sort_values(["security_id", "report_period"])
    val = pd.to_numeric(fin[value_col], errors="coerce")
    lag = fin.groupby("security_id")[value_col].transform(lambda s: pd.to_numeric(s, errors="coerce").shift(QUARTERS_3Y))
    cagr = np.where((lag > 0) & (val > 0), (val / lag) ** (1.0 / 3.0) - 1.0, np.nan)
    fin[factor_id] = cagr

    ctx2 = replace(ctx, financials=fin)
    asof = latest_financials_asof(ctx2)
    if asof.empty or factor_id not in asof.columns:
        return _empty()
    return make_output(asof["security_id"], asof["trade_date"], factor_id, asof[factor_id])


def _rev_yoy(ctx: FactorContext) -> pd.DataFrame:
    return _direct_yoy(ctx, "revenue_yoy", "REV_GROWTH_YOY")


def _np_yoy(ctx: FactorContext) -> pd.DataFrame:
    return _direct_yoy(ctx, "net_profit_yoy", "NP_GROWTH_YOY")


def _rev_3y(ctx: FactorContext) -> pd.DataFrame:
    return _cagr_asof(ctx, "total_revenue", "REV_GROWTH_3Y")


def _np_3y(ctx: FactorContext) -> pd.DataFrame:
    return _cagr_asof(ctx, "net_profit", "NP_GROWTH_3Y")


FACTORS: dict[str, FactorFn] = {
    "REV_GROWTH_YOY": _rev_yoy,
    "NP_GROWTH_YOY": _np_yoy,
    "REV_GROWTH_3Y": _rev_3y,
    "NP_GROWTH_3Y": _np_3y,
}
