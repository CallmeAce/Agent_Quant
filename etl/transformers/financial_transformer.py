"""
Financial statement transformer.

Merges Tushare fina_indicator / income / balancesheet / cashflow into the
unified ods_financial_statement contract (statement_type='ALL'), keyed by
(security_id, report_period). announce_date is preserved for point-in-time
correctness in factor computation and backtests.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Mapping, Optional

import numpy as np  # type: ignore
import pandas as pd  # type: ignore


def _keyed(df: Optional[pd.DataFrame], mapping: Mapping[str, str]) -> Optional[pd.DataFrame]:
    """Reduce a raw statement frame to (ts_code, end_date) + renamed columns."""
    if df is None or df.empty or "ts_code" not in df.columns or "end_date" not in df.columns:
        return None
    out = pd.DataFrame()
    out["ts_code"] = df["ts_code"].astype(str)
    out["end_date"] = pd.to_datetime(df["end_date"], errors="coerce")
    for raw_col, target in mapping.items():
        if raw_col not in df.columns:
            out[target] = pd.NaT if "announce" in target else np.nan
        elif "announce" in target:
            out[target] = pd.to_datetime(df[raw_col], errors="coerce")
        else:
            out[target] = pd.to_numeric(df[raw_col], errors="coerce")
    out = out.dropna(subset=["end_date"])
    out = out.sort_values("end_date").drop_duplicates(subset=["ts_code", "end_date"], keep="last")
    return out


def standardize_financials(
    security_map: Mapping[str, str],
    batch_id: str,
    source: str,
    fina_df: Optional[pd.DataFrame] = None,
    income_df: Optional[pd.DataFrame] = None,
    balancesheet_df: Optional[pd.DataFrame] = None,
    cashflow_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """Merge financial sources into the ods_financial_statement contract."""
    parts = [
        _keyed(fina_df, {
            "ann_date": "announce_date_raw",
            "roe_waa": "roe",
            "roa": "roa",
            "grossprofit_margin": "gross_margin",
            "netprofit_margin": "net_margin",
            "tr_yoy": "revenue_yoy",
            "netprofit_yoy": "net_profit_yoy",
            "basic_eps": "eps",
        }),
        _keyed(income_df, {
            "ann_date": "income_announce_date",
            "total_revenue": "total_revenue",
            "n_income_attr_p": "net_profit",
        }),
        _keyed(balancesheet_df, {
            "ann_date": "bs_announce_date",
            "total_assets": "total_assets",
            "total_liab": "total_liabilities",
            "total_hldr_eqy_exc_min_int": "total_equity",
        }),
        _keyed(cashflow_df, {
            "ann_date": "cf_announce_date",
            "n_cashflow_act": "operating_cashflow",
        }),
    ]
    parts = [p for p in parts if p is not None]
    if not parts:
        return pd.DataFrame()

    merged = parts[0]
    for p in parts[1:]:
        merged = merged.merge(p, on=["ts_code", "end_date"], how="outer", suffixes=("", "_r"))

    merged["security_id"] = merged["ts_code"].map(security_map)
    merged = merged[merged["security_id"].notna()].copy()
    if merged.empty:
        return pd.DataFrame()

    merged["report_period"] = merged["end_date"].dt.date
    announce = None
    for col in ["announce_date_raw", "income_announce_date", "bs_announce_date", "cf_announce_date"]:
        if col in merged.columns:
            announce = merged[col] if announce is None else announce.combine_first(merged[col])
    merged["announce_date"] = announce.dt.date if announce is not None else None

    merged["fiscal_year"] = merged["end_date"].dt.year
    merged["fiscal_quarter"] = (merged["end_date"].dt.month - 1) // 3 + 1
    merged["statement_type"] = "ALL"
    merged["source"] = source
    merged["ingest_batch_id"] = batch_id
    merged["updated_at"] = datetime.now(timezone.utc)

    cols = [
        "security_id", "report_period", "announce_date", "statement_type",
        "fiscal_year", "fiscal_quarter", "total_revenue", "net_profit",
        "total_assets", "total_liabilities", "total_equity", "operating_cashflow",
        "roe", "roa", "gross_margin", "net_margin", "eps", "revenue_yoy",
        "net_profit_yoy", "source", "ingest_batch_id", "updated_at",
    ]
    for col in cols:
        if col not in merged.columns:
            merged[col] = np.nan
    return merged[cols]  # type: ignore[return-value]
