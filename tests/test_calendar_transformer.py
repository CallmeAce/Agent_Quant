import pandas as pd

from etl.transformers.calendar_transformer import standardize_trade_calendar


def test_empty_returns_empty():
    assert standardize_trade_calendar(pd.DataFrame(), "SSE").empty


def test_maps_trade_cal_columns():
    raw = pd.DataFrame(
        [
            {"exchange": "SSE", "cal_date": "20240102", "is_open": 1, "pretrade_date": "20231229"},
            {"exchange": "SSE", "cal_date": "20240106", "is_open": 0, "pretrade_date": "20240105"},
        ]
    )
    out = standardize_trade_calendar(raw, "SSE")
    assert list(out.columns) == ["exchange", "trade_date", "is_trading_day", "previous_trading_date"]
    assert out.iloc[0]["is_trading_day"] == 1
    assert out.iloc[1]["is_trading_day"] == 0
    assert str(out.iloc[0]["previous_trading_date"]) == "2023-12-29"
