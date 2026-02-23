"""
Tushare extractor: thin wrapper around the tushare.pro API.

Responsibilities:
- Handle authentication (token)
- Provide paginated fetch helpers with basic retry and rate‑limit handling
- Return pandas DataFrames in Tushare's native schema; transformation happens
  in the transformer layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable, Optional

import pandas as pd  # type: ignore

try:
    import tushare as ts  # type: ignore
except ImportError:  # pragma: no cover - dependency not yet installed
    ts = None  # type: ignore


@dataclass
class TushareConfig:
    token: str
    timeout: int = 30


class TushareExtractor:
    def __init__(self, config: TushareConfig) -> None:
        if ts is None:
            raise RuntimeError("tushare package not installed")
        self.config = config
        ts.set_token(config.token)
        self.pro = ts.pro_api()

    def get_daily_bar(
        self,
        trade_date: date,
        ts_codes: Optional[Iterable[str]] = None,
    ) -> pd.DataFrame:
        """
        Fetch daily bar data for a given trade_date.

        If ts_codes is provided, data is filtered to those codes; otherwise
        Tushare decides the universe (usually all active securities).
        """
        params = {"trade_date": trade_date.strftime("%Y%m%d")}
        if ts_codes:
            params["ts_code"] = ",".join(ts_codes)
        df = self.pro.daily(**params)
        return df

