"""
QMT extractor.

This module defines a thin abstraction over QMT's APIs or local data access.
The actual integration details (Python API, DLL, local DB, etc.) are left
to be implemented depending on your QMT environment.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Iterable, Optional

import pandas as pd  # type: ignore


@dataclass
class QmtConfig:
    account_ids: Iterable[str]
    # Add connection parameters as needed (host/port/paths, etc.)


class QmtExtractor:
    def __init__(self, config: QmtConfig) -> None:
        self.config = config

    def get_positions(self, as_of: datetime) -> pd.DataFrame:
        """
        Return position snapshot for all configured accounts at the given time.

        Expected columns include at least:
        - account_id
        - qmt_code
        - quantity
        - available_qty
        - avg_cost
        - last_price
        """
        raise NotImplementedError("Integrate with your QMT environment here")

    def get_trades(self, trade_date: date) -> pd.DataFrame:
        """
        Return trades for the given date for all configured accounts.
        """
        raise NotImplementedError("Integrate with your QMT environment here")

