import os

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from etl.api.main import app
from etl.monitoring import record_job_run

pytestmark = pytest.mark.usefixtures("live_db")


@pytest.fixture()
def seeded_db(live_db, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", live_db)
    engine = create_engine(live_db, future=True)
    run_id = "__TEST_API_RUN__"
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO dim_factor (factor_id, name, category, status) VALUES ('PE_TTM','PE','valuation','active') ON CONFLICT (factor_id) DO NOTHING"))
        conn.execute(text("INSERT INTO dwd_factor_value (security_id,trade_date,factor_id,factor_value,value_type,calc_version,source) VALUES ('__T_API__','2024-01-02','PE_TTM',1.0,'zscore','v1','test') ON CONFLICT DO NOTHING"))
        conn.execute(text("INSERT INTO dm_strategy_signal (strategy_id,security_id,signal_time,signal_type,target_weight,source) VALUES ('CN_VALUE_MID_V1','__T_API__','2024-01-02','TARGET_WEIGHT',0.5,'test') ON CONFLICT DO NOTHING"))
        conn.execute(text("INSERT INTO dwd_backtest_run (run_id,strategy_id,start_date,end_date,cost_bps) VALUES (:r,'CN_VALUE_MID_V1','2024-01-01','2024-01-31',20) ON CONFLICT DO NOTHING"), {"r": run_id})
        conn.execute(text("INSERT INTO dwd_backtest_metrics (run_id,total_return,sharpe,max_drawdown) VALUES (:r,0.1,1.5,0.05) ON CONFLICT DO NOTHING"), {"r": run_id})
        conn.execute(text("INSERT INTO dwd_strategy_nav (run_id,trade_date,nav) VALUES (:r,'2024-01-02',1.01) ON CONFLICT DO NOTHING"), {"r": run_id})
    record_job_run(live_db, "test_job", "success", rows_affected=1, duration_seconds=0.1, message="ok")
    yield live_db
    with engine.begin() as conn:
        for t, col in [("dwd_factor_value", "security_id"), ("dm_strategy_signal", "security_id"), ("dwd_strategy_nav", "run_id"), ("dwd_backtest_metrics", "run_id"), ("dwd_backtest_run", "run_id")]:
            val = "__T_API__" if col == "security_id" else run_id
            conn.execute(text(f"DELETE FROM {t} WHERE {col}=:v"), {"v": val})
        conn.execute(text("DELETE FROM ops_job_run WHERE job_name='test_job'"))


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["database"] == "connected"


def test_system_status_and_jobs(client, seeded_db):
    s = client.get("/api/v1/system/status")
    assert s.status_code == 200
    body = s.json()
    assert any(f["table_name"] == "dwd_factor_value" for f in body["data_freshness"])
    j = client.get("/api/v1/jobs")
    assert j.status_code == 200
    assert any(row["job_name"] == "test_job" for row in j.json())


def test_factors_and_signals(client, seeded_db):
    f = client.get("/api/v1/factors")
    assert f.status_code == 200
    pe = next((x for x in f.json() if x["factor_id"] == "PE_TTM"), None)
    assert pe is not None and pe["row_count"] >= 1

    sig = client.get("/api/v1/signals?strategy_id=CN_VALUE_MID_V1")
    assert sig.status_code == 200
    assert any(x["security_id"] == "__T_API__" for x in sig.json())


def test_strategies_from_config(client):
    r = client.get("/api/v1/strategies")
    assert r.status_code == 200
    ids = {s["strategy_id"] for s in r.json()}
    assert {"CN_VALUE_MID_V1", "CN_MOM_SWING_V1"} <= ids


def test_backtests_list_and_detail(client, seeded_db):
    lst = client.get("/api/v1/backtests")
    assert lst.status_code == 200
    run_id = "__TEST_API_RUN__"
    assert any(x["run_id"] == run_id for x in lst.json())

    detail = client.get(f"/api/v1/backtests/{run_id}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["metrics"]["total_return"] == 0.1
    assert len(body["nav"]) >= 1

    missing = client.get("/api/v1/backtests/does-not-exist")
    assert missing.status_code == 404


@pytest.fixture()
def client(live_db, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", live_db)
    return TestClient(app)
