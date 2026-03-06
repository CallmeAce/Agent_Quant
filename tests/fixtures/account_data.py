"""
Account and position data fixtures for testing.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict

import pandas as pd


def create_sample_positions_df(
    account_ids: list[str] | None = None,
    ts_codes: list[str] | None = None,
) -> pd.DataFrame:
    """
    Create a sample positions DataFrame mimicking QMT position output.

    Parameters
    ----------
    account_ids : list[str], optional
        List of account IDs. Defaults to ['ACC001'].
    ts_codes : list[str], optional
        List of stock codes. Defaults to ['600000.SH', '000001.SZ'].

    Returns
    -------
    pd.DataFrame
        Sample positions data.
    """
    if account_ids is None:
        account_ids = ["ACC001"]
    if ts_codes is None:
        ts_codes = ["600000.SH", "000001.SZ"]

    data = {
        "account_id": [],
        "security_id": [],
        "quantity": [],
        "available_qty": [],
        "avg_cost": [],
        "market_price": [],
        "snapshot_time": [],
    }

    for acc_id in account_ids:
        for ts_code in ts_codes:
            data["account_id"].append(acc_id)
            data["security_id"].append(f"CN.{ts_code}")
            data["quantity"].append(10000)
            data["available_qty"].append(10000)
            data["avg_cost"].append(10.0)
            data["market_price"].append(10.5)
            data["snapshot_time"].append(datetime(2026, 1, 3, 15, 0, 0))

    return pd.DataFrame(data)


def create_sample_trades_df(
    account_ids: list[str] | None = None,
    ts_codes: list[str] | None = None,
    trade_date: str = "20260103",
) -> pd.DataFrame:
    """
    Create a sample trades DataFrame mimicking QMT trade output.

    Parameters
    ----------
    account_ids : list[str], optional
        List of account IDs. Defaults to ['ACC001'].
    ts_codes : list[str], optional
        List of stock codes. Defaults to ['600000.SH', '000001.SZ'].
    trade_date : str
        Trade date in YYYYMMDD format.

    Returns
    -------
    pd.DataFrame
        Sample trades data.
    """
    if account_ids is None:
        account_ids = ["ACC001"]
    if ts_codes is None:
        ts_codes = ["600000.SH", "000001.SZ"]

    data = {
        "trade_id": [],
        "order_id": [],
        "account_id": [],
        "security_id": [],
        "trade_time": [],
        "side": [],
        "price": [],
        "quantity": [],
        "amount": [],
        "fee": [],
        "tax": [],
    }

    for i, (acc_id, ts_code) in enumerate(zip(account_ids, ts_codes)):
        data["trade_id"].append(f"TR{i+1:04d}")
        data["order_id"].append(f"OR{i+1:04d}")
        data["account_id"].append(acc_id)
        data["security_id"].append(f"CN.{ts_code}")
        data["trade_time"].append(datetime(2026, 1, 3, 10, 30, 0))
        data["side"].append("buy")
        data["price"].append(10.0)
        data["quantity"].append(1000)
        data["amount"].append(10000.0)
        data["fee"].append(25.0)
        data["tax"].append(0.0)

    return pd.DataFrame(data)


def create_sample_account_equity_df(
    account_ids: list[str] | None = None,
    trade_date: str = "20260103",
) -> pd.DataFrame:
    """
    Create a sample account equity DataFrame.

    Parameters
    ----------
    account_ids : list[str], optional
        List of account IDs. Defaults to ['ACC001'].
    trade_date : str
        Trade date in YYYYMMDD format.

    Returns
    -------
    pd.DataFrame
        Sample equity data.
    """
    if account_ids is None:
        account_ids = ["ACC001"]

    data = {
        "account_id": account_ids,
        "trade_date": [trade_date] * len(account_ids),
        "total_equity": [1000000.0] * len(account_ids),
        "cash": [500000.0] * len(account_ids),
        "frozen_cash": [0.0] * len(account_ids),
        "market_value": [500000.0] * len(account_ids),
        "available_funds": [500000.0] * len(account_ids),
        "leverage_ratio": [1.0] * len(account_ids),
    }

    return pd.DataFrame(data)


def create_sample_qmt_config() -> dict:
    """
    Create a sample QMT configuration.

    Returns
    -------
    dict
        Sample QMT config.
    """
    return {
        "account_ids": ["ACC001", "ACC002"],
        "host": "localhost",
        "port": "9000",
    }
