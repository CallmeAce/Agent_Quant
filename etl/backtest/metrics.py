"""Backtest performance metrics from a NAV series."""

from __future__ import annotations

import numpy as np  # type: ignore
import pandas as pd  # type: ignore

TRADING_DAYS = 252


def compute_metrics(nav: pd.Series) -> dict:
    nav = pd.to_numeric(nav, errors="coerce").dropna()
    if len(nav) < 1:
        return {"total_return": 0.0, "annual_return": 0.0, "sharpe": 0.0, "max_drawdown": 0.0, "win_rate": 0.0}

    # Measure performance from initial capital of 1.0 (costs on the first
    # rebalance are therefore included in total return / drawdown).
    series = pd.concat([pd.Series([1.0]), nav], ignore_index=True)

    total_return = float(series.iloc[-1] / 1.0 - 1.0)
    n = len(series)
    annual_return = float((1.0 + total_return) ** (TRADING_DAYS / n) - 1.0) if n > 1 else 0.0

    daily = series.pct_change().dropna()
    std = float(daily.std())
    sharpe = float(daily.mean() / std * np.sqrt(TRADING_DAYS)) if std > 0 else 0.0

    peak = series.cummax()
    drawdown = (peak - series) / peak
    max_drawdown = float(drawdown.max())

    win_rate = float((daily > 0).mean()) if len(daily) else 0.0

    return {
        "total_return": total_return,
        "annual_return": annual_return,
        "sharpe": sharpe,
        "max_drawdown": max_drawdown,
        "win_rate": win_rate,
    }
