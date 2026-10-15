import pandas as pd

from etl.transformers.account_transformer import standardize_positions


def test_empty_input_returns_empty():
    out = standardize_positions(pd.DataFrame(), "b", "qmt")
    assert out.empty


def test_positions_derive_market_value_and_defaults():
    raw = pd.DataFrame(
        [
            {
                "account_id": "A1", "security_id": "CN.600000.SSE",
                "snapshot_time": "2026-01-02 15:00:00", "quantity": 100,
                "available_qty": 100, "avg_cost": 10.0, "market_price": 12.0,
            }
        ]
    )
    out = standardize_positions(raw, batch_id="b1", source="qmt")
    row = out.iloc[0]
    assert row["market_value"] == 1200.0
    assert row["unrealized_pnl"] == 0.0
    assert row["realized_pnl_daily"] == 0.0
    assert row["source"] == "qmt"
    assert row["ingest_batch_id"] == "b1"
    assert row["updated_at"].tzinfo is not None
