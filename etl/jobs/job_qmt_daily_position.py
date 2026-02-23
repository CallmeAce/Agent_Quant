"""
Job: load QMT end‑of‑day positions into ods_position_snapshot.
"""

from __future__ import annotations

from datetime import date, datetime

from etl.config import tables as tables_config  # type: ignore
from etl.extractors.qmt_extractor import QmtConfig, QmtExtractor
from etl.loaders.db_loader import DbConfig, DbLoader
from etl.transformers.account_transformer import standardize_positions


def generate_batch_id(trade_date: date) -> str:
    return f"qmt_positions_{trade_date.strftime('%Y%m%d')}_{datetime.utcnow().strftime('%H%M%S')}"


def run(trade_date: date, account_ids, db_url: str) -> None:
    """
    Entrypoint for the QMT daily position job.
    """
    batch_id = generate_batch_id(trade_date)
    extractor = QmtExtractor(QmtConfig(account_ids=account_ids))

    # In most QMT setups, we fetch as‑of time by using trade_date close time.
    # Here we use "now" as a placeholder.
    raw_df = extractor.get_positions(as_of=datetime.utcnow())

    std_df = standardize_positions(raw_df, batch_id=batch_id, source="qmt")

    loader = DbLoader(DbConfig(url=db_url), table_contracts=tables_config.CONTRACTS)
    loader.upsert("ods_position_snapshot", std_df, key_cols=["account_id", "security_id", "snapshot_time"])

