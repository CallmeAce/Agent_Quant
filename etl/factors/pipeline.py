"""Factor pipeline: run selected factors over a context and emit dwd_factor_value rows."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

import pandas as pd  # type: ignore

from etl.factors.base import FactorContext, cross_sectional_zscore
from etl.factors.registry import ALL_FACTORS

OUTPUT_COLUMNS = [
    "security_id", "trade_date", "factor_id", "factor_value",
    "value_type", "calc_version", "source", "updated_at",
]


def run_factors(
    ctx: FactorContext,
    factor_ids: List[str],
    zscore: bool = True,
    calc_version: str = "v1",
    source: str = "factor_engine",
) -> pd.DataFrame:
    frames: List[pd.DataFrame] = []
    now = datetime.now(timezone.utc)
    for fid in factor_ids:
        fn = ALL_FACTORS.get(fid)
        if fn is None:
            raise KeyError(f"unknown factor_id: {fid}")
        out = fn(ctx)
        if out is None or out.empty:
            continue
        out = out.copy()
        if zscore:
            out = cross_sectional_zscore(ctx, out)
        out["value_type"] = "zscore" if zscore else "raw"
        out["calc_version"] = calc_version
        out["source"] = source
        out["updated_at"] = now
        frames.append(out[OUTPUT_COLUMNS])

    if not frames:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)
    return pd.concat(frames, ignore_index=True)
