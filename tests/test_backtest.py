import numpy as np
import pandas as pd

from etl.backtest.engine import run_backtest
from etl.backtest.metrics import compute_metrics

DATES = pd.bdate_range("2023-01-02", periods=10)
A, B = "A", "B"


def _prices():
    rows = []
    for i, d in enumerate(DATES):
        rows.append({"security_id": A, "trade_date": d, "close_adj": 100.0 * (1.001 ** i)})
        rows.append({"security_id": B, "trade_date": d, "close_adj": 100.0})
    return pd.DataFrame(rows)


def _signals():
    return pd.DataFrame([
        {"strategy_id": "S1", "security_id": A, "signal_time": DATES[0], "target_weight": 1.0},
    ])


def test_engine_no_cost_compounds():
    res = run_backtest(_signals(), _prices(), cost_bps=0.0)
    expected = 1.001 ** 9 - 1.0
    assert abs(res["metrics"]["total_return"] - expected) < 1e-9
    assert res["metrics"]["max_drawdown"] == 0.0  # monotonic NAV
    assert not res["positions"].empty


def test_engine_with_cost():
    res = run_backtest(_signals(), _prices(), cost_bps=20.0)
    expected = 0.998 * 1.001 ** 9 - 1.0  # 1.0 turnover * 20bps charged on entry
    assert abs(res["metrics"]["total_return"] - expected) < 1e-9
    assert res["turnover"] == 1.0


def test_engine_benchmark_nav():
    bench = pd.DataFrame([{"trade_date": d, "close": 1000.0 * (1.002 ** i)} for i, d in enumerate(DATES)])
    res = run_backtest(_signals(), _prices(), benchmark=bench, cost_bps=0.0)
    assert res["metrics"]["benchmark_return"] > res["metrics"]["total_return"]
    assert res["nav"]["benchmark_nav"].notna().all()


def test_metrics_known_series():
    nav = pd.Series([1.0, 1.1, 1.05, 1.2])
    m = compute_metrics(nav)
    assert abs(m["total_return"] - 0.2) < 1e-9
    assert abs(m["max_drawdown"] - (1.1 - 1.05) / 1.1) < 1e-9
    assert m["win_rate"] > 0
