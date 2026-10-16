"""
Load a FactorContext from the analytical database.
"""

from __future__ import annotations

from datetime import date
from typing import List, Optional

import pandas as pd  # type: ignore
from sqlalchemy import create_engine, text  # type: ignore

from etl.factors.base import FactorContext


def _read(engine, sql: str, params: dict) -> pd.DataFrame:
    return pd.read_sql(text(sql), engine, params=params)


def load_context(
    db_url: str,
    security_ids: List[str],
    start_date: date,
    end_date: date,
    benchmark_index: Optional[str] = None,
) -> FactorContext:
    engine = create_engine(db_url, future=True)
    ids = list(security_ids)
    if not ids:
        return FactorContext(pd.DataFrame(), pd.DataFrame(), pd.DataFrame())

    prices = _read(
        engine,
        """
        SELECT security_id, trade_date, close, adj_factor, vol, amount
        FROM ods_daily_bar
        WHERE security_id = ANY(:ids) AND trade_date BETWEEN :s AND :e
        """,
        {"ids": ids, "s": start_date, "e": end_date},
    )
    if not prices.empty:
        adj = pd.to_numeric(prices["adj_factor"], errors="coerce").fillna(1.0)
        prices["close_adj"] = pd.to_numeric(prices["close"], errors="coerce") * adj

    daily_basic = _read(
        engine,
        """
        SELECT security_id, trade_date, pe_ttm, pb, ps_ttm, dv_ttm,
               turnover_rate, total_mv, circ_mv, volume_ratio
        FROM ods_daily_basic
        WHERE security_id = ANY(:ids) AND trade_date BETWEEN :s AND :e
        """,
        {"ids": ids, "s": start_date, "e": end_date},
    )

    financials = _read(
        engine,
        """
        SELECT security_id, report_period, announce_date, total_revenue, net_profit,
               total_assets, total_liabilities, total_equity, operating_cashflow,
               roe, roa, gross_margin, net_margin, revenue_yoy, net_profit_yoy, eps
        FROM ods_financial_statement
        WHERE security_id = ANY(:ids) AND statement_type = 'ALL'
        """,
        {"ids": ids, "s": start_date, "e": end_date},
    )

    index_close = None
    if benchmark_index:
        index_close = _read(
            engine,
            "SELECT trade_date, close FROM ods_index_daily WHERE index_id = :idx AND trade_date BETWEEN :s AND :e ORDER BY trade_date",
            {"idx": benchmark_index, "s": start_date, "e": end_date},
        )

    return FactorContext(prices=prices, daily_basic=daily_basic, financials=financials, index_close=index_close)
