"""
Database loader utilities.

Provides a simple abstraction to upsert pandas DataFrames into a relational
database according to the contracts defined in etl/config/tables.yml.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

import pandas as pd  # type: ignore
from sqlalchemy import create_engine  # type: ignore


@dataclass
class DbConfig:
    url: str  # e.g. postgresql+psycopg2://user:pass@host:5432/db


class DbLoader:
    def __init__(self, config: DbConfig, table_contracts: Mapping[str, dict]) -> None:
        self.engine = create_engine(config.url, future=True)
        self.table_contracts = table_contracts

    def upsert(self, table: str, df: pd.DataFrame, key_cols: Iterable[str]) -> None:
        """
        Simple batch upsert implementation.

        For MVP this can rely on database‑specific ON CONFLICT syntax configured
        at the DDL level; here we only perform batched inserts and assume
        constraints handle duplicates appropriately.
        """
        if df.empty:
            return
        df.to_sql(table, self.engine, if_exists="append", index=False, method="multi")

