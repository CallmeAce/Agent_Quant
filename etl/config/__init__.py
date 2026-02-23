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


CONTRACTS = load_table_contracts()

