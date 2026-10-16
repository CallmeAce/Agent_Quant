# Pipeline Runbook (implemented)

End-to-end data → factors → strategies → backtest → monitoring/dashboard pipeline.

## Stages

1. **Sync (ODS)** — `etl/jobs/job_sync_*.py`
   - `job_sync_security` → `dim_security`
   - `job_sync_trade_calendar` → `dim_trade_calendar`
   - `job_sync_index_daily` → `ods_index_daily` (benchmark)
   - `job_sync_daily_bar_range` → `ods_daily_bar` (adjusted prices)
   - `job_sync_daily_basic` → `ods_daily_basic` (valuation/liquidity/size)
   - `job_sync_financials` → `ods_financial_statement` (merged income/balancesheet/cashflow/fina_indicator, PIT via `announce_date`)

2. **Factors** — `etl/factors/` (30 factors) → `dwd_factor_value`
   - Config: `etl/config/factor_pipeline.yml` (factor ids + per-date winsorized z-score).
   - Job: `job_compute_factors`.

3. **Strategies** — `etl/strategies/` (composite z-score + filters + top-N) → `dm_strategy_signal`
   - Config: `etl/config/strategies.yml` (`CN_VALUE_MID_V1` monthly, `CN_MOM_SWING_V1` weekly).
   - Job: `job_generate_signals`.

4. **Backtest** — `etl/backtest/` (daily buy-and-hold drift, fixed bps turnover cost) → `dwd_backtest_run`, `dwd_backtest_metrics`, `dwd_strategy_nav`, `dwd_strategy_position`
   - Job: `job_run_backtest`.

5. **Monitoring** — `etl/monitoring.py` records `ops_job_run`; `v_data_freshness` view exposes data freshness.

6. **API + Dashboard** — `etl/api/main.py` (JSON API) + `etl/web/` (static monitoring + backtest dashboard, vendored ECharts).

## Pilot universe

`etl/config/universe_pilot.yml` — curated A-share `ts_codes` + `benchmark_index` (default `000300.SH`). Edit freely.

## One-shot bootstrap

```bash
export DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/quant_db
export TUSHARE_TOKEN=...
python -m etl.pipeline --start 2022-01-01 --end 2024-12-31
# reuse already-synced ODS data:
python -m etl.pipeline --start 2022-01-01 --end 2024-12-31 --skip-sync
```

## Scheduler (incremental)

`python -m etl` runs APScheduler cron jobs: daily bars/basic, weekly calendar/financials, then `compute_factors → generate_signals → run_backtest` with dependency gating. Every run is recorded to `ops_job_run`.

## API endpoints

- `GET /` dashboard; `GET /health`
- `GET /api/v1/system/status`, `/api/v1/system/freshness`, `/api/v1/jobs`
- `GET /api/v1/factors`, `/api/v1/strategies`, `/api/v1/signals`
- `GET /api/v1/backtests`, `/api/v1/backtests/{run_id}`

## Notes / current limitations

- Requires a Tushare token with `daily_basic` and `fina_indicator` access.
- Filters operate on z-score thresholds (tail screens), not raw units.
- Industry/size neutralization is not yet applied (raw + z-score only).
- Backtest is daily, fixed-cost, no slippage/limit-up-down or intraday fills.
