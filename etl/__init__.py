"""
ETL package for Agent_Quant.

This package provides a pluggable architecture for:
- Extractors: data source clients (Tushare, QMT, others)
- Transformers: business-specific cleaning and standardisation logic
- Loaders: batched writes to the analytical database
- Jobs: composable tasks orchestrated by Openclaw or a scheduler
"""

