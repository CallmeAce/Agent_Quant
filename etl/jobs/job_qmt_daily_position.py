"""
Job: load QMT end‑of‑day positions into ods_position_snapshot.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from etl.config import CONTRACTS  # type: ignore
from etl.extractors.qmt_extractor import QmtConfig, QmtExtractor
from etl.loaders.db_loader import DbConfig, DbLoader
from etl.transformers.account_transformer import standardize_positions


def generate_batch_id(trade_date: date) -> str:
    ts = datetime.now(timezone.utc).strftime("%H%M%S")
    return f"qmt_positions_{trade_date.strftime('%Y%m%d')}_{ts}"


def run(trade_date: date, account_ids, db_url: str) -> None:
    """
    Entrypoint for the QMT daily position job.
    """
    batch_id = generate_batch_id(trade_date)
    extractor = QmtExtractor(QmtConfig(account_ids=account_ids))

    # In most QMT setups, we fetch as‑of time by using trade_date close time.
    # Here we use "now" as a placeholder.
    raw_df = extractor.get_positions(as_of=datetime.now(timezone.utc))

    std_df = standardize_positions(raw_df, batch_id=batch_id, source="qmt")

    loader = DbLoader(DbConfig(url=db_url), table_contracts=CONTRACTS)
    loader.upsert("ods_position_snapshot", std_df, key_cols=["account_id", "security_id", "snapshot_time"])

