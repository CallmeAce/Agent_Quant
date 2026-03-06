"""
Pytest configuration and shared fixtures.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Generator

import pandas as pd
import pytest

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from etl.config import CONTRACTS


# =============================================================================
# Database Fixtures
# =============================================================================


@pytest.fixture
def test_db_url() -> str:
    """
    Provide an in-memory SQLite database URL for testing.

    Returns
    -------
    str
        SQLite connection URL.
    """
    return "sqlite:///:memory:"


@pytest.fixture
def test_db_config(test_db_url: str) -> dict:
    """
    Provide test database configuration.

    Parameters
    ----------
    test_db_url : str
        In-memory SQLite URL.

    Returns
    -------
    dict
        Database config dict.
    """
    return {"url": test_db_url}


# =============================================================================
# Config Fixtures
# =============================================================================


@pytest.fixture
def table_contracts() -> dict:
    """
    Load table contracts from etl/config/tables.yml.

    Returns
    -------
    dict
        Table contracts configuration.
    """
    return CONTRACTS


# =============================================================================
# Sample Data Fixtures
# =============================================================================


@pytest.fixture
def sample_daily_bar_df() -> pd.DataFrame:
    """
    Provide a sample daily bar DataFrame.

    Returns
    -------
    pd.DataFrame
        Sample market data.
    """
    from tests.fixtures.market_data import create_sample_daily_bar_df

    return create_sample_daily_bar_df()


@pytest.fixture
def sample_daily_bar_single_code_df() -> pd.DataFrame:
    """
    Provide a sample daily bar DataFrame with single stock code.

    Returns
    -------
    pd.DataFrame
        Sample market data for one stock.
    """
    from tests.fixtures.market_data import create_sample_daily_bar_df

    return create_sample_daily_bar_df(ts_codes=["600000.SH"])


@pytest.fixture
def sample_security_map() -> dict[str, str]:
    """
    Provide a sample ts_code to security_id mapping.

    Returns
    -------
    dict[str, str]
        Security mapping.
    """
    from tests.fixtures.market_data import create_sample_security_map

    return create_sample_security_map()


@pytest.fixture
def sample_dim_security_df() -> pd.DataFrame:
    """
    Provide a sample dim_security DataFrame.

    Returns
    -------
    pd.DataFrame
        Sample security dimension data.
    """
    from tests.fixtures.market_data import create_sample_dim_security_df

    return create_sample_dim_security_df()


@pytest.fixture
def sample_trade_calendar_df() -> pd.DataFrame:
    """
    Provide a sample trade calendar DataFrame.

    Returns
    -------
    pd.DataFrame
        Sample trade calendar.
    """
    from tests.fixtures.market_data import create_sample_trade_calendar_df

    return create_sample_trade_calendar_df()


@pytest.fixture
def sample_financial_statement_df() -> pd.DataFrame:
    """
    Provide a sample financial statement DataFrame.

    Returns
    -------
    pd.DataFrame
        Sample financial data.
    """
    from tests.fixtures.market_data import create_sample_financial_statement_df

    return create_sample_financial_statement_df()


@pytest.fixture
def sample_positions_df() -> pd.DataFrame:
    """
    Provide a sample positions DataFrame.

    Returns
    -------
    pd.DataFrame
        Sample position data.
    """
    from tests.fixtures.account_data import create_sample_positions_df

    return create_sample_positions_df()


@pytest.fixture
def sample_trades_df() -> pd.DataFrame:
    """
    Provide a sample trades DataFrame.

    Returns
    -------
    pd.DataFrame
        Sample trade data.
    """
    from tests.fixtures.account_data import create_sample_trades_df

    return create_sample_trades_df()


@pytest.fixture
def sample_account_equity_df() -> pd.DataFrame:
    """
    Provide a sample account equity DataFrame.

    Returns
    -------
    pd.DataFrame
        Sample equity data.
    """
    from tests.fixtures.account_data import create_sample_account_equity_df

    return create_sample_account_equity_df()


@pytest.fixture
def sample_batch_id() -> str:
    """
    Provide a sample batch ID.

    Returns
    -------
    str
        Batch identifier.
    """
    return "test_batch_20260103_143000"


@pytest.fixture
def sample_source() -> str:
    """
    Provide a sample data source label.

    Returns
    -------
    str
        Source label.
    """
    return "tushare"


# =============================================================================
# Mock Fixtures
# =============================================================================


@pytest.fixture
def mock_tushare_pro(mocker: Any) -> Any:
    """
    Mock the tushare.pro_api() for testing.

    Parameters
    ----------
    mocker : Any
        pytest-mock fixture.

    Returns
    -------
    Any
        Mocked pro API.
    """
    mock_pro = mocker.patch("etl.extractors.tushare_extractor.ts.pro_api")
    return mock_pro.return_value


@pytest.fixture
def mock_sqlalchemy_engine(mocker: Any) -> Any:
    """
    Mock sqlalchemy create_engine for testing.

    Parameters
    ----------
    mocker : Any
        pytest-mock fixture.

    Returns
    -------
    Any
        Mocked engine.
    """
    mock_engine = mocker.patch("etl.loaders.db_loader.create_engine")
    return mock_engine.return_value


# =============================================================================
# Date/Time Fixtures
# =============================================================================


@pytest.fixture
def sample_trade_date() -> Any:
    """
    Provide a sample trade date.

    Returns
    -------
    Any
        Date object.
    """
    from datetime import date

    return date(2026, 1, 3)


@pytest.fixture
def sample_batch_id_prefix() -> str:
    """
    Provide a sample batch ID prefix.

    Returns
    -------
    str
        Batch ID prefix.
    """
    return "tushare_daily_"


# =============================================================================
# Empty DataFrame Fixtures
# =============================================================================


@pytest.fixture
def empty_daily_bar_df() -> pd.DataFrame:
    """
    Provide an empty daily bar DataFrame.

    Returns
    -------
    pd.DataFrame
        Empty DataFrame.
    """
    return pd.DataFrame(
        {
            "ts_code": [],
            "trade_date": [],
            "open": [],
            "high": [],
            "low": [],
            "close": [],
            "pre_close": [],
            "change": [],
            "pct_change": [],
            "vol": [],
            "amount": [],
            "adj_factor": [],
        }
    )


@pytest.fixture
def empty_positions_df() -> pd.DataFrame:
    """
    Provide an empty positions DataFrame.

    Returns
    -------
    pd.DataFrame
        Empty DataFrame.
    """
    return pd.DataFrame(
        {
            "account_id": [],
            "security_id": [],
            "quantity": [],
            "available_qty": [],
            "avg_cost": [],
            "market_price": [],
            "snapshot_time": [],
        }
    )
