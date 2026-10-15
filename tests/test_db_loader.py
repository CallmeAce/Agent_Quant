import pandas as pd
from sqlalchemy import create_engine, text

from etl.config import CONTRACTS
from etl.loaders.db_loader import DbConfig, DbLoader

TEST_ID = "__PYTEST_SEC__"


def _frame(name: str) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "security_id": TEST_ID, "ts_code": "TEST.SZ", "symbol": "TEST",
                "name": name, "exchange": "SZSE", "security_type": "A",
                "list_date": None, "delist_date": None, "status": "listed",
                "currency": "CNY",
            }
        ]
    )


def test_upsert_is_idempotent_and_updates(live_db):
    loader = DbLoader(DbConfig(url=live_db), table_contracts=CONTRACTS)

    loader.upsert("dim_security", _frame("OldName"), key_cols=["security_id"])
    loader.upsert("dim_security", _frame("NewName"), key_cols=["security_id"])

    engine = create_engine(live_db, future=True)
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                text("SELECT name FROM dim_security WHERE security_id = :i"),
                {"i": TEST_ID},
            ).mappings().all()
            conn.execute(
                text("DELETE FROM dim_security WHERE security_id = :i"), {"i": TEST_ID}
            )
            conn.commit()
    finally:
        engine.dispose()

    assert len(rows) == 1
    assert rows[0]["name"] == "NewName"


def test_upsert_empty_frame_is_noop(live_db):
    loader = DbLoader(DbConfig(url=live_db), table_contracts=CONTRACTS)
    loader.upsert("dim_security", pd.DataFrame(), key_cols=["security_id"])  # no error
