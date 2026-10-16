import numpy as np
import pandas as pd
import pytest

from etl.factors.base import FactorContext
from etl.factors.registry import ALL_FACTORS, FACTOR_CATEGORY
from etl.factors.pipeline import run_factors, OUTPUT_COLUMNS

DATES = pd.bdate_range("2023-01-02", periods=130)
SEC_A = "CN.600000.SSE"
SEC_B = "CN.000001.SZ"


def _prices():
    rows = []
    for i, d in enumerate(DATES):
        # SEC_A monotonic increasing; SEC_B sinusoidal
        px_a = 100.0 + i
        px_b = 100.0 + 10.0 * np.sin(i / 5.0)
        rows.append({"security_id": SEC_A, "trade_date": d, "close_adj": px_a, "vol": 1000.0, "amount": 1e6})
        rows.append({"security_id": SEC_B, "trade_date": d, "close_adj": px_b, "vol": 2000.0, "amount": 2e6})
    return pd.DataFrame(rows)


def _daily_basic():
    rows = []
    for d in DATES:
        rows.append({"security_id": SEC_A, "trade_date": d, "pe_ttm": 10.0, "pb": 2.0, "ps_ttm": 3.0,
                     "dv_ttm": 1.5, "turnover_rate": 1.0, "total_mv": 1e9, "circ_mv": 5e8, "volume_ratio": 1.0})
        rows.append({"security_id": SEC_B, "trade_date": d, "pe_ttm": 20.0, "pb": 4.0, "ps_ttm": 6.0,
                     "dv_ttm": 0.5, "turnover_rate": 3.0, "total_mv": 1e10, "circ_mv": 5e9, "volume_ratio": 1.0})
    return pd.DataFrame(rows)


def _financials():
    rows = []
    for q in range(17):  # 2019-03-31 .. 2023-03-31 quarterly history
        period = pd.Timestamp("2019-03-31") + pd.DateOffset(months=3 * q)
        announce = period + pd.Timedelta(days=45)
        rev = 1000.0 * (1.1 ** q)
        for sec, mult in [(SEC_A, 1.0), (SEC_B, 2.0)]:
            rows.append({
                "security_id": sec, "report_period": period.date(), "announce_date": announce.date(),
                "total_revenue": rev * mult, "net_profit": 100.0 * mult,
                "total_assets": 5000.0 * mult, "total_liabilities": 3000.0 * mult,
                "total_equity": 2000.0 * mult, "operating_cashflow": 120.0 * mult,
                "roe": 12.0, "roa": 5.0, "gross_margin": 30.0, "net_margin": 20.0,
                "revenue_yoy": 10.0, "net_profit_yoy": 8.0, "eps": 1.0,
            })
    return pd.DataFrame(rows)


def _index_close():
    # benchmark equals SEC_A prices -> beta(SEC_A) == 1
    return pd.DataFrame([{"trade_date": d, "close": 100.0 + i} for i, d in enumerate(DATES)])


def build_context() -> FactorContext:
    return FactorContext(
        prices=_prices(), daily_basic=_daily_basic(), financials=_financials(), index_close=_index_close()
    )


def _value(out, sec, date, fid):
    m = out[(out["security_id"] == sec) & (out["trade_date"] == pd.Timestamp(date).date()) & (out["factor_id"] == fid)]
    assert len(m) == 1, f"missing {fid} for {sec} on {date}"
    return float(m["factor_value"].iloc[0])


def test_registry_has_30_factors_with_categories():
    assert len(ALL_FACTORS) == 30
    assert set(FACTOR_CATEGORY.values()) == {"valuation", "quality", "growth", "momentum", "volatility", "liquidity"}


def test_all_factors_run_and_emit_contract_columns():
    ctx = build_context()
    for fid, fn in ALL_FACTORS.items():
        out = fn(ctx)
        assert set(out.columns) == {"security_id", "trade_date", "factor_id", "factor_value"}, fid
        assert (out["factor_id"] == fid).all()


def test_momentum_value():
    out = ALL_FACTORS["MOM_20D"](build_context())
    # close[20]/close[0]-1 = 120/100-1 = 0.2
    assert abs(_value(out, SEC_A, DATES[20], "MOM_20D") - 0.2) < 1e-9


def test_valuation_raw_and_peg():
    ctx = build_context()
    pe = ALL_FACTORS["PE_TTM"](ctx)
    assert abs(_value(pe, SEC_A, DATES[5], "PE_TTM") - 10.0) < 1e-9
    ey = ALL_FACTORS["EARNINGS_YIELD"](ctx)
    assert abs(_value(ey, SEC_A, DATES[5], "EARNINGS_YIELD") - 0.1) < 1e-9
    peg = ALL_FACTORS["PEG"](ctx)
    # pe_ttm(10) / net_profit_yoy(8) = 1.25
    assert abs(_value(peg, SEC_A, DATES[5], "PEG") - 1.25) < 1e-9


def test_quality_debt_to_equity_and_roe():
    ctx = build_context()
    dte = ALL_FACTORS["DEBT_TO_EQUITY"](ctx)
    assert abs(_value(dte, SEC_A, DATES[5], "DEBT_TO_EQUITY") - 1.5) < 1e-9  # 3000/2000
    roe = ALL_FACTORS["ROE_TTM"](ctx)
    assert abs(_value(roe, SEC_A, DATES[5], "ROE_TTM") - 12.0) < 1e-9  # stored roe


def test_growth_yoy_and_cagr():
    ctx = build_context()
    yoy = ALL_FACTORS["REV_GROWTH_YOY"](ctx)
    assert abs(_value(yoy, SEC_A, DATES[5], "REV_GROWTH_YOY") - 10.0) < 1e-9
    cagr = ALL_FACTORS["REV_GROWTH_3Y"](ctx)
    # revenue grows 10% per quarter -> 3y (12 quarters) CAGR = 1.1^4 - 1
    expected = 1.1 ** 4 - 1
    assert abs(_value(cagr, SEC_A, DATES[5], "REV_GROWTH_3Y") - expected) < 1e-6


def test_volatility_beta_and_drawdown():
    ctx = build_context()
    beta = ALL_FACTORS["BETA_120D"](ctx)
    # SEC_A tracks benchmark exactly -> beta ~ 1
    assert abs(_value(beta, SEC_A, DATES[125], "BETA_120D") - 1.0) < 1e-6
    dd = ALL_FACTORS["MAX_DRAWDOWN_120D"](ctx)
    # SEC_A monotonic increasing -> drawdown 0
    assert abs(_value(dd, SEC_A, DATES[125], "MAX_DRAWDOWN_120D")) < 1e-9
    vol = ALL_FACTORS["VOLATILITY_20D"](ctx)
    # SEC_B oscillates -> volatility positive
    assert _value(vol, SEC_B, DATES[125], "VOLATILITY_20D") > 0


def test_size_and_liquidity():
    ctx = build_context()
    mv = ALL_FACTORS["LOG_TOTAL_MV"](ctx)
    assert abs(_value(mv, SEC_A, DATES[5], "LOG_TOTAL_MV") - np.log(1e9)) < 1e-6
    ill = ALL_FACTORS["ILLIQUIDITY_20D"](ctx)
    assert _value(ill, SEC_A, DATES[125], "ILLIQUIDITY_20D") >= 0


def test_pipeline_output_columns_and_zscore_mean_zero():
    ctx = build_context()
    ids = ["PE_TTM", "PB", "MOM_20D", "ROE_TTM", "LOG_TOTAL_MV"]
    out = run_factors(ctx, ids, zscore=True)
    assert list(out.columns) == OUTPUT_COLUMNS
    # per-date z-score -> mean ~ 0 for each (date, factor)
    grp = out.groupby(["trade_date", "factor_id"])["factor_value"].mean()
    assert (grp.abs() < 1e-6).all()
