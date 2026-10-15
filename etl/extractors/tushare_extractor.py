"""
Tushare extractor: thin wrapper around the tushare.pro API.

Responsibilities:
- Handle authentication (token)
- Provide paginated fetch helpers with basic retry and rate‑limit handling
- Return pandas DataFrames in Tushare's native schema; transformation happens
  in the transformer layer.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import date
from typing import Any, Iterable, Optional

import pandas as pd  # type: ignore

try:
    import tushare as ts  # type: ignore
except ImportError:  # pragma: no cover - dependency not yet installed
    ts = None  # type: ignore

logger = logging.getLogger(__name__)


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

    def _call(self, api_name: str, max_retries: int = 3, **params: Any) -> pd.DataFrame:
        """
        Invoke a Tushare pro endpoint with exponential backoff on transient
        errors / rate limits. Date-scoped queries return the full result in a
        single call, so no offset pagination is required here.
        """
        last_err: Optional[Exception] = None
        for attempt in range(max_retries):
            try:
                return getattr(self.pro, api_name)(**params)
            except Exception as e:  # rate limit / transient network error
                last_err = e
                wait = 2 ** attempt
                logger.warning(
                    "Tushare %s failed (attempt %d/%d): %s; retrying in %ds",
                    api_name, attempt + 1, max_retries, e, wait,
                )
                time.sleep(wait)
        assert last_err is not None
        raise last_err

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
        params: dict = {"trade_date": trade_date.strftime("%Y%m%d")}
        if ts_codes:
            params["ts_code"] = ",".join(ts_codes)
        return self._call("daily", **params)

    def get_adj_factor(self, trade_date: date) -> pd.DataFrame:
        """
        Fetch adjustment factors for all securities on a given trade_date.

        Returns a frame with at least `ts_code` and `adj_factor` columns.
        """
        return self._call("adj_factor", trade_date=trade_date.strftime("%Y%m%d"))

    def get_stock_basic(self, list_status: str = "L") -> pd.DataFrame:
        """
        Fetch the security master list (ts_code, symbol, name, exchange, ...).
        """
        return self._call("stock_basic", exchange="", list_status=list_status)

