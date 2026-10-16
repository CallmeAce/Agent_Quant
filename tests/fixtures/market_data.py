"""
Market data fixtures for testing.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Dict

import pandas as pd


def create_sample_daily_bar_df(
    ts_codes: list[str] | None = None,
    trade_date: str = "20260101",
) -> pd.DataFrame:
    """
    Create a sample daily bar DataFrame mimicking Tushare pro.daily() output.

    Parameters
    ----------
    ts_codes : list[str], optional
        List of stock codes. Defaults to ['600000.SH', '000001.SZ'].
    trade_date : str
        Trade date in YYYYMMDD format.

    Returns
    -------
    pd.DataFrame
        Sample daily bar data.
    """
    if ts_codes is None:
        ts_codes = ["600000.SH", "000001.SZ", "000002.SZ"]

    data = {
        "ts_code": ts_codes,
        "trade_date": [trade_date] * len(ts_codes),
        "open": [10.0 + i * 0.5 for i in range(len(ts_codes))],
        "high": [10.8 + i * 0.5 for i in range(len(ts_codes))],
        "low": [9.5 + i * 0.5 for i in range(len(ts_codes))],
        "close": [10.2 + i * 0.5 for i in range(len(ts_codes))],
        "pre_close": [10.0 + i * 0.5 for i in range(len(ts_codes))],
        "change": [0.2] * len(ts_codes),
        "pct_change": [2.0] * len(ts_codes),
        "vol": [1000000 + i * 500000 for i in range(len(ts_codes))],
        "amount": [10200000 + i * 5000000 for i in range(len(ts_codes))],
        "adj_factor": [1.0] * len(ts_codes),
    }

    return pd.DataFrame(data)


def create_sample_security_map() -> Dict[str, str]:
    """
    Create a sample ts_code -> security_id mapping.

    Returns
    -------
    Dict[str, str]
        Mapping dictionary.
    """
    return {
        "600000.SH": "CN.600000.SSE",
        "000001.SZ": "CN.000001.SZSE",
        "000002.SZ": "CN.000002.SZSE",
        "600519.SH": "CN.600519.SSE",
    }


def create_sample_dim_security_df() -> pd.DataFrame:
    """
    Create a sample dim_security DataFrame.

    Returns
    -------
    pd.DataFrame
        Sample dimension data.
    """
    return pd.DataFrame(
        {
            "security_id": [
                "CN.600000.SSE",
                "CN.000001.SZSE",
                "CN.000002.SZSE",
                "CN.600519.SSE",
            ],
            "ts_code": ["600000.SH", "000001.SZ", "000002.SZ", "600519.SH"],
            "symbol": ["600000", "000001", "000002", "600519"],
            "name": ["浦发银行", "平安银行", "万科A", "贵州茅台"],
            "exchange": ["SSE", "SZSE", "SZSE", "SSE"],
            "security_type": ["stock"] * 4,
            "list_date": ["1999-11-10", "1991-04-03", "1991-01-29", "2001-08-27"],
            "status": ["listed"] * 4,
            "currency": ["CNY"] * 4,
        }
    )


def create_sample_trade_calendar_df() -> pd.DataFrame:
    """
    Create a sample trade calendar DataFrame.

    Returns
    -------
    pd.DataFrame
        Sample trade calendar.
    """
    return pd.DataFrame(
        {
            "exchange": ["SSE"] * 3,
            "trade_date": ["2026-01-02", "2026-01-03", "2026-01-06"],
            "is_trading_day": [1, 1, 1],
            "week_of_year": [1, 1, 2],
            "month": [1, 1, 1],
            "quarter": [1, 1, 1],
            "year": [2026, 2026, 2026],
        }
    )


def create_sample_financial_statement_df() -> pd.DataFrame:
    """
    Create a sample financial statement DataFrame.

    Returns
    -------
    pd.DataFrame
        Sample financial data.
    """
    return pd.DataFrame(
        {
            "ts_code": ["600000.SH", "000001.SZ"],
            "report_period": ["2025-12-31", "2025-12-31"],
            "announce_date": ["2026-03-01", "2026-03-01"],
            "statement_type": ["ALL", "ALL"],
            "fiscal_year": [2025, 2025],
            "fiscal_quarter": [4, 4],
            "total_revenue": [1000000000.0, 800000000.0],
            "net_profit": [150000000.0, 120000000.0],
            "total_assets": [5000000000.0, 4000000000.0],
            "total_liabilities": [2000000000.0, 1500000000.0],
            "operating_cashflow": [200000000.0, 160000000.0],
            "roe": [15.0, 14.0],
            "gross_margin": [30.0, 28.0],
            "eps": [1.5, 1.2],
            "net_profit_yoy": [10.0, 8.0],
        }
    )
