"""
Vectorized daily backtest engine.

Holds target weights between rebalances with buy-and-hold drift; charges a fixed
one-way cost (bps) on turnover at each rebalance. Produces NAV, positions, and
performance metrics.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd  # type: ignore

from etl.backtest.metrics import compute_metrics


def _close_matrix(prices: pd.DataFrame) -> pd.DataFrame:
    df = prices.copy()
    df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.normalize()
    close = df.pivot_table(index="trade_date", columns="security_id", values="close_adj", aggfunc="last")
    return close.sort_index()


def _rebalance_map(signals: pd.DataFrame) -> dict:
    sig = signals.copy()
    sig["d"] = pd.to_datetime(sig["signal_time"]).dt.normalize()
    out: dict = {}
    for d, grp in sig.groupby("d"):
        weights: dict = {}
        for _, row in grp.iterrows():
            weights[row["security_id"]] = weights.get(row["security_id"], 0.0) + float(row["target_weight"])
        out[d] = weights
    return out


def run_backtest(
    signals: pd.DataFrame,
    prices: pd.DataFrame,
    benchmark: Optional[pd.DataFrame] = None,
    cost_bps: float = 20.0,
) -> dict:
    close = _close_matrix(prices)
    if close.empty or signals.empty:
        return {"nav": pd.DataFrame(), "positions": pd.DataFrame(), "metrics": compute_metrics(pd.Series(dtype=float)), "turnover": 0.0}

    ret = close.pct_change().fillna(0.0)
    rebalance = _rebalance_map(signals)

    bench_nav = None
    if benchmark is not None and not benchmark.empty:
        b = benchmark.copy()
        b["trade_date"] = pd.to_datetime(b["trade_date"]).dt.normalize()
        b = b.sort_values("trade_date")
        base = float(b["close"].iloc[0])
        bench_nav = dict(zip(b["trade_date"], b["close"] / base))

    weights: dict = {}
    nav = 1.0
    nav_rows = []
    pos_rows = []
    turnover_total = 0.0

    for d in close.index:
        cost = 0.0
        if d in rebalance:
            target = rebalance[d]
            secs = set(target) | set(weights)
            turnover = sum(abs(target.get(s, 0.0) - weights.get(s, 0.0)) for s in secs)
            turnover_total += turnover
            cost = turnover * cost_bps / 10000.0
            weights = dict(target)

        r = 0.0
        for s, w in weights.items():
            if s in ret.columns:
                r += w * float(ret.at[d, s])
        nav *= 1.0 + r
        if cost:
            nav *= 1.0 - cost

        if weights:
            denom = 1.0 + r
            weights = {
                s: (w * (1.0 + (float(ret.at[d, s]) if s in ret.columns else 0.0)) / denom if denom != 0 else w)
                for s, w in weights.items()
            }

        nav_rows.append({"trade_date": d, "nav": nav, "benchmark_nav": bench_nav.get(d) if bench_nav else None})
        if d in rebalance:
            for s, w in rebalance[d].items():
                pos_rows.append({"security_id": s, "trade_date": d, "weight": w})

    nav_df = pd.DataFrame(nav_rows)
    pos_df = pd.DataFrame(pos_rows, columns=["security_id", "trade_date", "weight"])
    metrics = compute_metrics(nav_df["nav"]) if not nav_df.empty else compute_metrics(pd.Series(dtype=float))
    metrics["turnover"] = turnover_total
    if bench_nav and nav_df["benchmark_nav"].notna().any():
        bnav = nav_df["benchmark_nav"].dropna()
        metrics["benchmark_return"] = float(bnav.iloc[-1] / bnav.iloc[0] - 1.0) if len(bnav) > 1 else 0.0
    else:
        metrics["benchmark_return"] = 0.0

    return {"nav": nav_df, "positions": pos_df, "metrics": metrics, "turnover": turnover_total}
