"""
Strategy engine base.

A strategy turns z-scored factor values into target-weight signals on rebalance
dates. Composite score = weighted sum of z-scores; filters exclude securities
whose z-score breaches a threshold; top-N selected with equal weights.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

import numpy as np  # type: ignore
import pandas as pd  # type: ignore

SIGNAL_COLUMNS = [
    "strategy_id", "security_id", "signal_time", "signal_type", "direction",
    "target_weight", "price_hint_min", "price_hint_max", "valid_from", "valid_to",
    "comment", "source", "created_at",
]


@dataclass
class StrategyContext:
    factors: pd.DataFrame  # security_id, trade_date, factor_id, factor_value (z-scored)
    prices: pd.DataFrame  # security_id, trade_date, close_adj


@dataclass
class StrategyConfig:
    strategy_id: str
    factor_weights: dict
    filters: list = field(default_factory=list)  # [{factor_id, op, threshold}]
    top_n: int = 20
    rebalance: str = "monthly"  # monthly | weekly
    direction: str = "BUY"


def rebalance_dates(prices: pd.DataFrame, freq: str) -> List:
    dates = sorted(pd.to_datetime(prices["trade_date"]).dt.normalize().unique())
    if not dates:
        return []
    s = pd.Series(dates)
    if freq == "weekly":
        key = s.dt.isocalendar().week.astype(str) + s.dt.year.astype(str)
    else:  # monthly
        key = s.dt.year.astype(str) + s.dt.month.astype(str)
    df = pd.DataFrame({"date": s, "key": key.values})
    return df.groupby("key", as_index=False).last()["date"].tolist()


def _apply_filters(pivot: pd.DataFrame, filters: list) -> pd.DataFrame:
    keep = pivot.copy()
    for f in filters:
        col = f["factor_id"]
        if col not in keep.columns:
            continue
        vals = keep[col]
        op = f["op"]
        thr = f["threshold"]
        mask = (vals > thr) if op == ">" else (vals < thr)
        keep = keep[~mask.fillna(False)]
    return keep


class CompositeStrategy:
    def __init__(self, config: StrategyConfig):
        self.config = config

    def generate_signals(self, ctx: StrategyContext) -> pd.DataFrame:
        cfg = self.config
        dates = rebalance_dates(ctx.prices, cfg.rebalance)
        if not dates:
            return pd.DataFrame(columns=SIGNAL_COLUMNS)

        fac = ctx.factors.copy()
        fac["trade_date"] = pd.to_datetime(fac["trade_date"]).dt.normalize()
        now = datetime.now(timezone.utc)
        rows: List[dict] = []

        for i, reb_date in enumerate(dates):
            day = fac[fac["trade_date"] == reb_date]
            if day.empty:
                continue
            pivot = day.pivot_table(index="security_id", columns="factor_id", values="factor_value", aggfunc="first")
            pivot = _apply_filters(pivot, cfg.filters)
            if pivot.empty:
                continue
            score = pd.Series(0.0, index=pivot.index)
            for fid, w in cfg.factor_weights.items():
                if fid in pivot.columns:
                    score = score + w * pivot[fid].fillna(0.0)
            top = score.sort_values(ascending=False).head(cfg.top_n)
            if top.empty:
                continue
            weight = 1.0 / len(top)
            valid_to = dates[i + 1] if i + 1 < len(dates) else reb_date + pd.Timedelta(days=365)
            for sec, sc in top.items():
                rows.append({
                    "strategy_id": cfg.strategy_id,
                    "security_id": sec,
                    "signal_time": reb_date,
                    "signal_type": "TARGET_WEIGHT",
                    "direction": cfg.direction,
                    "target_weight": round(weight, 4),
                    "price_hint_min": None,
                    "price_hint_max": None,
                    "valid_from": reb_date,
                    "valid_to": valid_to,
                    "comment": f"score={sc:.4f}",
                    "source": "strategy",
                    "created_at": now,
                })

        return pd.DataFrame(rows, columns=SIGNAL_COLUMNS)
