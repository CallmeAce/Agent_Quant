"""
Database loader utilities.

Provides a simple abstraction to upsert pandas DataFrames into a relational
database according to the contracts defined in etl/config/tables.yml.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

import pandas as pd  # type: ignore
from sqlalchemy import create_engine, MetaData, Table  # type: ignore
from sqlalchemy.dialects.postgresql import insert as pg_insert  # type: ignore


@dataclass
class DbConfig:
    url: str  # e.g. postgresql+psycopg2://user:pass@host:5432/db


class DbLoader:
    def __init__(self, config: DbConfig, table_contracts: Mapping[str, dict]) -> None:
        self.engine = create_engine(config.url, future=True)
        self.table_contracts = table_contracts
        self.metadata = MetaData()

    def _get_table(self, name: str) -> Table:
        if name not in self.metadata.tables:
            self.metadata.reflect(bind=self.engine, only=[name])
        return self.metadata.tables[name]

    def upsert(self, table: str, df: pd.DataFrame, key_cols: Iterable[str]) -> None:
        """
        Batched upsert using PostgreSQL ON CONFLICT DO UPDATE.

        Conflict keys are taken from the table contract's primary_key when
        available, falling back to the caller-provided key_cols.
        """
        if df.empty:
            return

        tbl = self._get_table(table)
        contract = self.table_contracts.get(table, {})
        keys = list(contract.get("primary_key") or []) or list(key_cols)
        update_cols = [c.name for c in tbl.columns if c.name not in keys]

        records = df.to_dict(orient="records")
        with self.engine.begin() as conn:
            stmt = pg_insert(tbl).values(records)
            if update_cols:
                stmt = stmt.on_conflict_do_update(
                    index_elements=keys,
                    set_={c: stmt.excluded[c] for c in update_cols},
                )
            else:
                stmt = stmt.on_conflict_do_nothing(index_elements=keys)
            conn.execute(stmt)

