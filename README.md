Agent Quant Platform
====================

This repository hosts an Openclaw-agent-driven quantitative investment platform
targeting CN A-share and HK equity markets with daily-frequency stock selection
and trading signals.

Current focus:

- Core business requirements and data contracts (BRD layer)
- Data model for QMT + Tushare as primary data sources
- ETL architecture and Python skeleton for data ingestion and transformation

Key directories:

- `docs/` – Business and data design documents (strategy catalog, data contracts, agent use cases, MVP scope)
- `etl/` – Python ETL skeleton (extractors, transformers, loaders, jobs)

This repo is designed to be extended with:

- Backend API services (FastAPI or similar)
- Frontend applications for admin and end users
- Strategy implementation and factor libraries

