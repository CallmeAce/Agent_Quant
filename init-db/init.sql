-- Initialize database schema for Openclaw Quant Platform
-- This script runs automatically when the PostgreSQL container first starts

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Dimension: Trade Calendar
CREATE TABLE IF NOT EXISTS dim_trade_calendar (
    exchange VARCHAR(20) NOT NULL,
    trade_date DATE NOT NULL,
    is_trading_day INTEGER NOT NULL DEFAULT 1,
    previous_trading_date DATE,
    next_trading_date DATE,
    week_of_year INTEGER,
    month INTEGER,
    quarter INTEGER,
    year INTEGER,
    PRIMARY KEY (exchange, trade_date)
);

-- Dimension: Security
CREATE TABLE IF NOT EXISTS dim_security (
    security_id VARCHAR(50) PRIMARY KEY,
    ts_code VARCHAR(20),
    qmt_code VARCHAR(50),
    symbol VARCHAR(20),
    name VARCHAR(100),
    exchange VARCHAR(20),
    security_type VARCHAR(20),
    list_date DATE,
    delist_date DATE,
    status VARCHAR(20) DEFAULT 'listed',
    currency VARCHAR(10) DEFAULT 'CNY',
    lot_size INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dimension: Industry
CREATE TABLE IF NOT EXISTS dim_industry (
    industry_code VARCHAR(50) PRIMARY KEY,
    industry_name VARCHAR(100),
    industry_level INTEGER,
    source VARCHAR(20)
);

-- Security-Industry Mapping
CREATE TABLE IF NOT EXISTS dim_security_industry_map (
    security_id VARCHAR(50) NOT NULL,
    industry_code VARCHAR(50) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    PRIMARY KEY (security_id, industry_code, start_date)
);

-- ODS: Daily Bar
CREATE TABLE IF NOT EXISTS ods_daily_bar (
    security_id VARCHAR(50) NOT NULL,
    trade_date DATE NOT NULL,
    open DECIMAL(18,4),
    high DECIMAL(18,4),
    low DECIMAL(18,4),
    close DECIMAL(18,4),
    pre_close DECIMAL(18,4),
    change DECIMAL(18,4),
    pct_change DECIMAL(10,4),
    vol DECIMAL(20,2),
    amount DECIMAL(20,4),
    adj_factor DECIMAL(18,8),
    source VARCHAR(20),
    ingest_batch_id VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (security_id, trade_date)
);

-- ODS: Financial Statement
CREATE TABLE IF NOT EXISTS ods_financial_statement (
    security_id VARCHAR(50) NOT NULL,
    report_period DATE NOT NULL,
    announce_date DATE,
    statement_type VARCHAR(10) NOT NULL,
    fiscal_year INTEGER,
    fiscal_quarter INTEGER,
    total_revenue DECIMAL(20,4),
    net_profit DECIMAL(20,4),
    total_assets DECIMAL(20,4),
    total_liabilities DECIMAL(20,4),
    operating_cashflow DECIMAL(20,4),
    roe DECIMAL(10,4),
    gross_margin DECIMAL(10,4),
    eps DECIMAL(10,4),
    net_profit_yoy DECIMAL(10,4),
    source VARCHAR(20),
    ingest_batch_id VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (security_id, report_period, statement_type)
);

-- ODS: Account Equity Daily
CREATE TABLE IF NOT EXISTS ods_account_equity_daily (
    account_id VARCHAR(50) NOT NULL,
    trade_date DATE NOT NULL,
    total_equity DECIMAL(20,4),
    cash DECIMAL(20,4),
    frozen_cash DECIMAL(20,4),
    market_value DECIMAL(20,4),
    available_funds DECIMAL(20,4),
    leverage_ratio DECIMAL(10,4),
    source VARCHAR(20),
    ingest_batch_id VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (account_id, trade_date)
);

-- ODS: Position Snapshot
CREATE TABLE IF NOT EXISTS ods_position_snapshot (
    account_id VARCHAR(50) NOT NULL,
    security_id VARCHAR(50) NOT NULL,
    snapshot_time TIMESTAMP NOT NULL,
    quantity DECIMAL(20,4),
    available_qty DECIMAL(20,4),
    avg_cost DECIMAL(18,4),
    market_price DECIMAL(18,4),
    market_value DECIMAL(20,4),
    unrealized_pnl DECIMAL(20,4),
    realized_pnl_daily DECIMAL(20,4),
    source VARCHAR(20),
    ingest_batch_id VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (account_id, security_id, snapshot_time)
);

-- ODS: Trade
CREATE TABLE IF NOT EXISTS ods_trade (
    trade_id VARCHAR(50) PRIMARY KEY,
    order_id VARCHAR(50),
    account_id VARCHAR(50),
    security_id VARCHAR(50),
    trade_time TIMESTAMP,
    side VARCHAR(10),
    price DECIMAL(18,4),
    quantity DECIMAL(20,4),
    amount DECIMAL(20,4),
    fee DECIMAL(18,4),
    tax DECIMAL(18,4),
    source VARCHAR(20),
    ingest_batch_id VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- DWD: Factor Value
CREATE TABLE IF NOT EXISTS dwd_factor_value (
    security_id VARCHAR(50) NOT NULL,
    trade_date DATE NOT NULL,
    factor_id VARCHAR(50) NOT NULL,
    factor_value DECIMAL(20,6),
    value_type VARCHAR(20),
    calc_version VARCHAR(50),
    source VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (security_id, trade_date, factor_id)
);

-- DM: Strategy Signal
CREATE TABLE IF NOT EXISTS dm_strategy_signal (
    strategy_id VARCHAR(50) NOT NULL,
    security_id VARCHAR(50),
    signal_time TIMESTAMP NOT NULL,
    signal_type VARCHAR(20) NOT NULL,
    direction VARCHAR(10),
    target_weight DECIMAL(10,4),
    price_hint_min DECIMAL(18,4),
    price_hint_max DECIMAL(18,4),
    valid_from TIMESTAMP,
    valid_to TIMESTAMP,
    comment TEXT,
    source VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (strategy_id, security_id, signal_time, signal_type)
);

-- Dimension: Factor (metadata)
CREATE TABLE IF NOT EXISTS dim_factor (
    factor_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100),
    category VARCHAR(30),
    description TEXT,
    universe VARCHAR(50),
    update_freq VARCHAR(20),
    source_tables TEXT,
    formula_reference VARCHAR(255),
    status VARCHAR(20) DEFAULT 'active'
);

-- Dimension: Strategy (metadata)
CREATE TABLE IF NOT EXISTS dim_strategy (
    strategy_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100),
    style_tags TEXT,
    market VARCHAR(20),
    universe_rule_ref VARCHAR(255),
    factor_set TEXT,
    rebalance_freq VARCHAR(20),
    target_holding_period VARCHAR(20),
    risk_constraints_ref VARCHAR(255),
    status VARCHAR(20) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_ods_daily_bar_trade_date ON ods_daily_bar(trade_date);
CREATE INDEX IF NOT EXISTS idx_ods_daily_bar_security_id ON ods_daily_bar(security_id);
CREATE INDEX IF NOT EXISTS idx_dwd_factor_value_trade_date ON dwd_factor_value(trade_date);
CREATE INDEX IF NOT EXISTS idx_dwd_factor_value_factor_id ON dwd_factor_value(factor_id);
CREATE INDEX IF NOT EXISTS idx_dm_strategy_signal_strategy_id ON dm_strategy_signal(strategy_id);
CREATE INDEX IF NOT EXISTS idx_dm_strategy_signal_signal_time ON dm_strategy_signal(signal_time);

-- Insert default factor metadata
INSERT INTO dim_factor (factor_id, name, category, description, update_freq, status) VALUES
    ('PE_TTM', '滚动市盈率', 'valuation', 'Trailing twelve months P/E ratio', 'daily', 'active'),
    ('PB', '市净率', 'valuation', 'Price to Book ratio', 'daily', 'active'),
    ('PS_TTM', '滚动市销率', 'valuation', 'Trailing twelve months P/S ratio', 'daily', 'active'),
    ('ROE', '净资产收益率', 'quality', 'Return on Equity', 'quarterly', 'active'),
    ('ROA', '资产收益率', 'quality', 'Return on Assets', 'quarterly', 'active'),
    ('GROSS_MARGIN', '毛利率', 'quality', 'Gross Profit Margin', 'quarterly', 'active'),
    ('MOM_20D', '20 日动量', 'momentum', '20-day price momentum', 'daily', 'active'),
    ('MOM_60D', '60 日动量', 'momentum', '60-day price momentum', 'daily', 'active'),
    ('VOLATILITY_20D', '20 日波动率', 'volatility', '20-day historical volatility', 'daily', 'active'),
    ('TURNOVER_20D', '20 日换手率', 'liquidity', '20-day average turnover rate', 'daily', 'active')
ON CONFLICT (factor_id) DO NOTHING;
