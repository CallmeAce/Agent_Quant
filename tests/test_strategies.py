import pandas as pd

from etl.strategies.base import CompositeStrategy, StrategyConfig, SIGNAL_COLUMNS, rebalance_dates
from etl.strategies.registry import build_strategies
from etl.config import CONTRACTS

SEC_A, SEC_B, SEC_C, SEC_FILTERED = "S_A", "S_B", "S_C", "S_FILTERED"
DATES = pd.bdate_range("2023-01-02", periods=40)  # spans Jan + Feb only


def _prices():
    rows = [{"security_id": s, "trade_date": d, "close_adj": 100.0} for d in DATES for s in [SEC_A, SEC_B, SEC_C, SEC_FILTERED]]
    return pd.DataFrame(rows)


def _factors_for(reb_dates):
    rows = []
    for d in reb_dates:
        # SEC_A strong value+quality; SEC_FILTERED has extreme leverage (z=3)
        data = {
            SEC_A: {"EARNINGS_YIELD": 2.0, "BOOK_YIELD": 2.0, "DIVIDEND_YIELD_TTM": 1.0, "ROE_TTM": 2.0, "NET_MARGIN": 1.0, "REV_GROWTH_YOY": 1.0, "DEBT_TO_EQUITY": 0.0, "LOG_TOTAL_MV": 1.0, "TURNOVER_20D": 1.0, "MOM_20D": 0.0, "MOM_60D": 0.0, "VOL_MOM_20D": 0.0},
            SEC_B: {"EARNINGS_YIELD": 0.5, "BOOK_YIELD": 0.5, "DIVIDEND_YIELD_TTM": 0.0, "ROE_TTM": 0.5, "NET_MARGIN": 0.0, "REV_GROWTH_YOY": 0.0, "DEBT_TO_EQUITY": 0.0, "LOG_TOTAL_MV": 1.0, "TURNOVER_20D": 1.0, "MOM_20D": 0.0, "MOM_60D": 0.0, "VOL_MOM_20D": 0.0},
            SEC_C: {"EARNINGS_YIELD": -1.0, "BOOK_YIELD": -1.0, "DIVIDEND_YIELD_TTM": 0.0, "ROE_TTM": -1.0, "NET_MARGIN": 0.0, "REV_GROWTH_YOY": 0.0, "DEBT_TO_EQUITY": 0.0, "LOG_TOTAL_MV": 1.0, "TURNOVER_20D": 1.0, "MOM_20D": 0.0, "MOM_60D": 0.0, "VOL_MOM_20D": 0.0},
            SEC_FILTERED: {"EARNINGS_YIELD": 3.0, "BOOK_YIELD": 3.0, "DIVIDEND_YIELD_TTM": 1.0, "ROE_TTM": 2.0, "NET_MARGIN": 1.0, "REV_GROWTH_YOY": 1.0, "DEBT_TO_EQUITY": 3.0, "LOG_TOTAL_MV": 1.0, "TURNOVER_20D": 1.0, "MOM_20D": 0.0, "MOM_60D": 0.0, "VOL_MOM_20D": 0.0},
        }
        for sec, fmap in data.items():
            for fid, val in fmap.items():
                rows.append({"security_id": sec, "trade_date": d, "factor_id": fid, "factor_value": val})
    return pd.DataFrame(rows)


def _ctx():
    prices = _prices()
    reb = rebalance_dates(prices, "monthly")
    return prices, _factors_for(reb), reb


def test_registry_builds_two_strategies():
    strategies = build_strategies()
    assert set(strategies) == {"CN_VALUE_MID_V1", "CN_MOM_SWING_V1"}


def test_value_mid_filters_and_ranks():
    prices, factors, reb = _ctx()
    assert len(reb) == 2  # end of Jan, end of Feb
    cfg = StrategyConfig(
        strategy_id="CN_VALUE_MID_V1",
        factor_weights={"EARNINGS_YIELD": 0.3, "BOOK_YIELD": 0.2, "DIVIDEND_YIELD_TTM": 0.1, "ROE_TTM": 0.2, "NET_MARGIN": 0.1, "REV_GROWTH_YOY": 0.1},
        filters=[{"factor_id": "DEBT_TO_EQUITY", "op": ">", "threshold": 2.0}],
        top_n=10, rebalance="monthly",
    )
    out = CompositeStrategy(cfg).generate_signals(type("C", (), {"factors": factors, "prices": prices}))
    assert list(out.columns) == SIGNAL_COLUMNS
    assert SEC_FILTERED not in set(out["security_id"])  # extreme leverage excluded
    assert SEC_A in set(out["security_id"])
    # SEC_A ranks above SEC_C
    assert set(out["security_id"]) >= {SEC_A, SEC_B}
    # equal weights sum to ~1 per rebalance date (4-dp rounding tolerated)
    for _, grp in out.groupby("signal_time"):
        assert abs(grp["target_weight"].sum() - 1.0) < 1e-2


def test_signal_columns_subset_of_contract():
    prices, factors, reb = _ctx()
    cfg = StrategyConfig(strategy_id="X", factor_weights={"EARNINGS_YIELD": 1.0}, top_n=5, rebalance="monthly")
    out = CompositeStrategy(cfg).generate_signals(type("C", (), {"factors": factors, "prices": prices}))
    assert set(out.columns) <= set(CONTRACTS["dm_strategy_signal"]["fields"])


def test_mom_swing_size_filter():
    prices = _prices()
    reb = rebalance_dates(prices, "weekly")
    rows = []
    for d in reb:
        for sec, mv in [(SEC_A, 1.0), (SEC_B, 1.0), (SEC_C, -2.0)]:  # SEC_C too small -> filtered
            rows.append({"security_id": sec, "trade_date": d, "factor_id": "MOM_20D", "factor_value": 1.0})
            rows.append({"security_id": sec, "trade_date": d, "factor_id": "LOG_TOTAL_MV", "factor_value": mv})
            rows.append({"security_id": sec, "trade_date": d, "factor_id": "TURNOVER_20D", "factor_value": 1.0})
    factors = pd.DataFrame(rows)
    cfg = StrategyConfig(
        strategy_id="CN_MOM_SWING_V1",
        factor_weights={"MOM_20D": 1.0},
        filters=[{"factor_id": "LOG_TOTAL_MV", "op": "<", "threshold": -1.0}],
        top_n=10, rebalance="weekly",
    )
    out = CompositeStrategy(cfg).generate_signals(type("C", (), {"factors": factors, "prices": prices}))
    assert SEC_C not in set(out["security_id"])
    assert {SEC_A, SEC_B} <= set(out["security_id"])
