"""
Configuration helpers for ETL, including table contracts.
"""

from __future__ import annotations

from pathlib import Path

import yaml  # type: ignore


BASE_DIR = Path(__file__).resolve().parent


def load_table_contracts() -> dict:
    path = BASE_DIR / "tables.yml"
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_universe(name: str = "universe_pilot") -> dict:
    """Load a pilot universe config (ts_codes + benchmark_index)."""
    path = BASE_DIR / f"{name}.yml"
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return {
        "ts_codes": list(data.get("ts_codes", [])),
        "benchmark_index": data.get("benchmark_index", "000300.SH"),
    }


def load_factor_pipeline() -> dict:
    """Load the factor pipeline config (factor_ids + zscore flag)."""
    path = BASE_DIR / "factor_pipeline.yml"
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return {
        "factor_ids": list(data.get("factors", [])),
        "zscore": bool(data.get("zscore", True)),
        "calc_version": data.get("calc_version", "v1"),
    }


CONTRACTS = load_table_contracts()

