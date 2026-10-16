import pandas as pd

from etl.transformers.financial_transformer import standardize_financials

SMAP = {"600000.SH": "CN.600000.SSE"}


def test_empty_when_no_sources():
    out = standardize_financials(SMAP, "b", "tushare")
    assert out.empty


def test_merges_sources_into_one_row():
    fina = pd.DataFrame(
        [{"ts_code": "600000.SH", "ann_date": "20240330", "end_date": "20231231",
          "roe_waa": 12.5, "grossprofit_margin": 30.0, "netprofit_margin": 20.0,
          "tr_yoy": 8.0, "netprofit_yoy": 10.0, "basic_eps": 1.2}]
    )
    income = pd.DataFrame(
        [{"ts_code": "600000.SH", "ann_date": "20240330", "end_date": "20231231",
          "total_revenue": 1000.0, "n_income_attr_p": 200.0}]
    )
    balance = pd.DataFrame(
        [{"ts_code": "600000.SH", "ann_date": "20240330", "end_date": "20231231",
          "total_assets": 5000.0, "total_liab": 3000.0, "total_hldr_eqy_exc_min_int": 2000.0}]
    )
    cash = pd.DataFrame(
        [{"ts_code": "600000.SH", "ann_date": "20240330", "end_date": "20231231",
          "n_cashflow_act": 150.0}]
    )
    out = standardize_financials(
        SMAP, "b1", "tushare",
        fina_df=fina, income_df=income, balancesheet_df=balance, cashflow_df=cash,
    )
    assert len(out) == 1
    r = out.iloc[0]
    assert r["security_id"] == "CN.600000.SSE"
    assert r["statement_type"] == "ALL"
    assert r["fiscal_year"] == 2023 and r["fiscal_quarter"] == 4
    assert r["total_revenue"] == 1000.0
    assert r["net_profit"] == 200.0
    assert r["total_equity"] == 2000.0
    assert r["operating_cashflow"] == 150.0
    assert r["roe"] == 12.5
    assert r["net_margin"] == 20.0
    assert r["revenue_yoy"] == 8.0
    assert str(r["announce_date"]) == "2024-03-30"


def test_unmapped_security_dropped():
    income = pd.DataFrame(
        [{"ts_code": "999999.XX", "end_date": "20231231", "total_revenue": 1, "n_income_attr_p": 1}]
    )
    out = standardize_financials(SMAP, "b", "tushare", income_df=income)
    assert out.empty
