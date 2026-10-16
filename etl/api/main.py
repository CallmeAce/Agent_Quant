"""
FastAPI backend for the Openclaw Quant Platform.

DB-backed endpoints for system monitoring, factors, strategies, signals, and
backtest results. Reads DATABASE_URL from the environment.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, text  # type: ignore

from etl.config import load_strategies  # type: ignore
from etl.monitoring import get_data_freshness, get_recent_job_runs, get_system_status

app = FastAPI(title="Openclaw Quant API", version="0.2.0")


def _db_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise HTTPException(status_code=503, detail="DATABASE_URL not configured")
    return url


def _query(sql: str, params: Optional[dict] = None) -> list:
    engine = create_engine(_db_url(), future=True)
    with engine.connect() as conn:
        rows = conn.execute(text(sql), params or {}).mappings().all()
    return [dict(r) for r in rows]


@app.get("/")
async def root():
    return {"message": "Openclaw Quant API", "version": "0.2.0"}


@app.get("/health")
async def health_check():
    try:
        _query("SELECT 1 AS ok")
        db = "connected"
    except HTTPException:
        db = "not_configured"
    except Exception:
        db = "error"
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc), "database": db}


@app.get("/api/v1/system/status")
async def system_status():
    return get_system_status(_db_url())


@app.get("/api/v1/system/freshness")
async def data_freshness():
    return get_data_freshness(_db_url())


@app.get("/api/v1/jobs")
async def list_jobs(limit: int = 50):
    return get_recent_job_runs(_db_url(), limit=limit)


@app.get("/api/v1/factors")
async def list_factors():
    meta = _query("SELECT factor_id, name, category, status FROM dim_factor ORDER BY category, factor_id")
    counts = _query("SELECT factor_id, COUNT(*) AS row_count, MAX(trade_date) AS latest_date FROM dwd_factor_value GROUP BY factor_id")
    count_map = {c["factor_id"]: c for c in counts}
    for f in meta:
        c = count_map.get(f["factor_id"], {})
        f["row_count"] = c.get("row_count", 0)
        f["latest_date"] = c.get("latest_date")
    return meta


@app.get("/api/v1/strategies")
async def list_strategies_endpoint():
    cfg = load_strategies()
    out = []
    for sid, c in cfg.items():
        out.append({
            "strategy_id": sid,
            "rebalance": c.get("rebalance"),
            "top_n": c.get("top_n"),
            "factor_weights": c.get("factor_weights", {}),
        })
    return out


@app.get("/api/v1/signals")
async def list_signals(strategy_id: Optional[str] = None, limit: int = 100):
    if strategy_id:
        return _query(
            "SELECT strategy_id, security_id, signal_time, target_weight, direction FROM dm_strategy_signal "
            "WHERE strategy_id = :sid ORDER BY signal_time DESC LIMIT :lim",
            {"sid": strategy_id, "lim": limit},
        )
    return _query(
        "SELECT strategy_id, security_id, signal_time, target_weight, direction FROM dm_strategy_signal "
        "ORDER BY signal_time DESC LIMIT :lim",
        {"lim": limit},
    )


@app.get("/api/v1/backtests")
async def list_backtests(limit: int = 50):
    return _query(
        "SELECT r.run_id, r.strategy_id, r.start_date, r.end_date, r.cost_bps, r.created_at, "
        "m.total_return, m.annual_return, m.sharpe, m.max_drawdown, m.benchmark_return "
        "FROM dwd_backtest_run r LEFT JOIN dwd_backtest_metrics m ON r.run_id = m.run_id "
        "ORDER BY r.created_at DESC LIMIT :lim",
        {"lim": limit},
    )


@app.get("/api/v1/backtests/{run_id}")
async def get_backtest(run_id: str):
    run = _query("SELECT * FROM dwd_backtest_run WHERE run_id = :r", {"r": run_id})
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    metrics = _query("SELECT * FROM dwd_backtest_metrics WHERE run_id = :r", {"r": run_id})
    nav = _query("SELECT trade_date, nav, benchmark_nav FROM dwd_strategy_nav WHERE run_id = :r ORDER BY trade_date", {"r": run_id})
    positions = _query("SELECT security_id, trade_date, weight FROM dwd_strategy_position WHERE run_id = :r ORDER BY trade_date, weight DESC", {"r": run_id})
    return {"run": run[0], "metrics": metrics[0] if metrics else {}, "nav": nav, "positions": positions}
