import numpy as np
import pandas as pd

from etl.transformers.market_transformer import (
    standardize_daily_bar,
    standardize_daily_basic,
    standardize_index_daily,
)


def _raw() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "ts_code": "600000.SH", "trade_date": "20260102", "open": 10,
                "high": 11, "low": 10, "close": 11, "pre_close": 10,
                "vol": 5, "amount": 3,
            },
            {
                "ts_code": "000001.SZ", "trade_date": "20260102", "open": 0,
                "high": 0, "low": 0, "close": 0, "pre_close": 0,
                "vol": 1, "amount": 1,
            },
            {
                "ts_code": "999999.XX", "trade_date": "20260102", "open": 1,
                "high": 1, "low": 1, "close": 1, "pre_close": 1,
                "vol": 1, "amount": 1,
            },
        ]
    )


def _run(adj_df=None) -> pd.DataFrame:
    return standardize_daily_bar(
        _raw(),
        security_map={"600000.SH": "CN.600000.SSE", "000001.SZ": "CN.000001.SZ"},
        batch_id="b1",
        source="tushare",
        adj_df=adj_df,
    ).reset_index(drop=True)


def test_empty_input_returns_empty():
    out = standardize_daily_bar(pd.DataFrame(), {}, "b", "tushare")
    assert out.empty


def test_pct_change_and_units():
    out = _run()
    r0 = out.iloc[0]
    assert r0["security_id"] == "CN.600000.SSE"
    assert abs(r0["pct_change"] - 0.1) < 1e-9
    assert r0["vol"] == 500  # lots -> shares
    assert r0["amount"] == 3000  # k-yuan -> yuan


def test_zero_pre_close_gives_nan_not_inf():
    out = _run()
    assert np.isnan(out.iloc[1]["pct_change"])


def test_adj_factor_merged_or_null():
    adj = pd.DataFrame([{"ts_code": "600000.SH", "adj_factor": 1.234}])
    out = _run(adj_df=adj)
    assert abs(out.iloc[0]["adj_factor"] - 1.234) < 1e-9
    # missing factor -> NULL, never 1.0
    assert pd.isna(out.iloc[1]["adj_factor"])


def test_unmapped_security_is_nan():
    out = _run()
    assert pd.isna(out.iloc[2]["security_id"])


def test_updated_at_is_tz_aware():
    out = _run()
    assert out["updated_at"].iloc[0].tzinfo is not None


def test_daily_basic_maps_and_defaults_missing_columns():
    raw = pd.DataFrame(
        [
            {"ts_code": "600000.SH", "trade_date": "20260102", "close": 10,
             "turnover_rate": 1.5, "pe_ttm": 8.0, "pb": 1.1, "total_mv": 1e6}
        ]
    )
    out = standardize_daily_basic(raw, {"600000.SH": "CN.600000.SSE"}, "b", "tushare")
    r = out.iloc[0]
    assert r["security_id"] == "CN.600000.SSE"
    assert r["pe_ttm"] == 8.0
    # missing columns are present as NaN, not KeyError
    assert "dv_ttm" in out.columns and pd.isna(r["dv_ttm"])
    assert out["updated_at"].iloc[0].tzinfo is not None


def test_index_daily_pct_and_units():
    raw = pd.DataFrame(
        [
            {"ts_code": "000300.SH", "trade_date": "20260102", "open": 100, "high": 110,
             "low": 100, "close": 110, "pre_close": 100, "vol": 5, "amount": 3}
        ]
    )
    out = standardize_index_daily(raw, "b", "tushare")
    r = out.iloc[0]
    assert r["index_id"] == "000300.SH"
    assert abs(r["pct_change"] - 0.1) < 1e-9
    assert r["vol"] == 500
    assert r["amount"] == 3000
