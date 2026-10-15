import pandas as pd

from etl.config import CONTRACTS
from etl.jobs.job_sync_security import _to_dim_security_df
from etl.transformers.account_transformer import standardize_positions
from etl.transformers.market_transformer import standardize_daily_bar


def test_every_contract_has_pk_and_fields():
    assert CONTRACTS, "no contracts loaded"
    for name, spec in CONTRACTS.items():
        pk = spec.get("primary_key")
        fields = spec.get("fields")
        assert isinstance(pk, list) and pk, f"{name}: missing primary_key"
        assert isinstance(fields, dict) and fields, f"{name}: missing fields"
        for col in pk:
            assert col in fields, f"{name}: primary_key {col} not in fields"


def _daily_bar_columns() -> set:
    raw = pd.DataFrame(
        [
            {
                "ts_code": "600000.SH", "trade_date": "20260102", "open": 1,
                "high": 1, "low": 1, "close": 1, "pre_close": 1,
                "vol": 1, "amount": 1,
            }
        ]
    )
    out = standardize_daily_bar(raw, {"600000.SH": "CN.600000.SSE"}, "b", "tushare")
    return set(out.columns)


def _dim_security_columns() -> set:
    raw = pd.DataFrame(
        [{"ts_code": "600000.SH", "symbol": "600000", "name": "x", "exchange": "SSE"}]
    )
    return set(_to_dim_security_df(raw).columns)


def _position_columns() -> set:
    raw = pd.DataFrame(
        [
            {
                "account_id": "A1", "security_id": "S1", "snapshot_time": "2026-01-02 15:00:00",
                "quantity": 1, "available_qty": 1, "avg_cost": 1, "market_price": 1,
            }
        ]
    )
    return set(standardize_positions(raw, "b", "qmt").columns)


def test_transformer_columns_are_subset_of_contracts():
    # Guards against drift: a transformer must never emit a column that is not
    # declared in the table contract (which would break the upsert).
    pairs = {
        "ods_daily_bar": _daily_bar_columns(),
        "dim_security": _dim_security_columns(),
        "ods_position_snapshot": _position_columns(),
    }
    for table, cols in pairs.items():
        contract_fields = set(CONTRACTS[table]["fields"])
        missing = cols - contract_fields
        assert not missing, f"{table}: transformer emits undeclared columns {missing}"
