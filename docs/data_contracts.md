## 核心数据契约（Core Data Contracts）

本文件对应 todo「在BRD基础上为核心实体制定更细的字段级数据契约」，结合 QMT + Tushare 为主的数据源。

类型说明（抽象类型，可映射到具体数据库）：
- `STRING` / `INT` / `BIGINT`
- `DATE` / `DATETIME`
- `DECIMAL(p,s)`（精度按实际需要调整）

---

## 1. 证券与维度实体

### 1.1 `dim_security`

- **描述**：统一证券维度表，兼容 A 股/港股/指数等。
- **主键**：`security_id`

| 字段名        | 类型            | 说明                                 |
|---------------|-----------------|--------------------------------------|
| security_id   | STRING          | 内部统一ID，如 `CN.600000.SSE`       |
| ts_code       | STRING          | Tushare 代码，如 `600000.SH`        |
| qmt_code      | STRING          | QMT 代码，含交易所标识              |
| symbol        | STRING          | 短代码（无交易所）                  |
| name          | STRING          | 中文简称                             |
| exchange      | STRING          | SSE/SZSE/HKEX 等                    |
| security_type | STRING          | stock/index/fund/bond 等            |
| list_date     | DATE            | 上市日期                             |
| delist_date   | DATE NULL       | 退市日期                             |
| status        | STRING          | listed/suspended/delisted           |
| currency      | STRING          | CNY/HKD 等                           |
| lot_size      | INT             | 最小交易单位（港股一手股数）        |
| created_at    | DATETIME        | 创建时间                             |
| updated_at    | DATETIME        | 更新时间                             |

---

### 1.2 `dim_trade_calendar`

- **描述**：每个交易所的交易日历。
- **联合主键**：`exchange`, `trade_date`

| 字段名             | 类型     | 说明                          |
|--------------------|----------|-------------------------------|
| exchange           | STRING   | 交易所                        |
| trade_date         | DATE     | 日期                          |
| is_trading_day     | INT      | 1=交易日, 0=非交易日          |
| previous_trading_date | DATE  | 上一交易日                    |
| next_trading_date  | DATE     | 下一交易日                    |
| week_of_year       | INT      | 周序号                        |
| month              | INT      | 月                            |
| quarter            | INT      | 季度                          |
| year               | INT      | 年                            |

---

### 1.3 `dim_industry` 与 `dim_security_industry_map`

`dim_industry`：

| 字段名        | 类型   | 说明                     |
|---------------|--------|--------------------------|
| industry_code | STRING | 行业代码（申万/中信等）  |
| industry_name | STRING | 行业名称                 |
| industry_level| INT    | 1/2/3 级                |
| source        | STRING | sw/citic 等             |

`dim_security_industry_map`（支持行业变迁）：

| 字段名        | 类型   | 说明                          |
|---------------|--------|-------------------------------|
| security_id   | STRING | 证券ID                        |
| industry_code | STRING | 行业代码                      |
| start_date    | DATE   | 生效开始日                    |
| end_date      | DATE   | 生效结束日（NULL=当前有效）  |

---

## 2. 行情与基础数据（Tushare 主）

### 2.1 `ods_daily_bar`

- **描述**：统一日线行情，Tushare 为主，QMT 可补充。
- **联合主键**：`security_id`, `trade_date`

| 字段名      | 类型          | 说明                                |
|-------------|---------------|-------------------------------------|
| security_id | STRING        | 证券ID                              |
| trade_date  | DATE          | 交易日期                            |
| open        | DECIMAL(18,4) | 开盘价                              |
| high        | DECIMAL(18,4) | 最高价                              |
| low         | DECIMAL(18,4) | 最低价                              |
| close       | DECIMAL(18,4) | 收盘价                              |
| pre_close   | DECIMAL(18,4) | 前一交易日收盘价                    |
| change      | DECIMAL(18,4) | 涨跌额 = close - pre_close         |
| pct_change  | DECIMAL(10,4) | 涨跌幅（小数或百分比，统一约定）    |
| vol         | DECIMAL(20,2) | 成交量（股或手，统一约定）         |
| amount      | DECIMAL(20,4) | 成交额                              |
| adj_factor  | DECIMAL(18,8) | 复权因子                            |
| source      | STRING        | tushare/qmt/merged                  |
| ingest_batch_id | STRING    | 批次号                              |
| updated_at  | DATETIME      | 更新时间                            |

---

### 2.2 `ods_minute_bar`（预留）

- **联合主键**：`security_id`, `trade_datetime`

| 字段名        | 类型          | 说明          |
|---------------|---------------|---------------|
| security_id   | STRING        | 证券ID        |
| trade_datetime| DATETIME      | 分钟时间戳    |
| open/high/low/close | DECIMAL(18,4) | K 线价格 |
| vol           | DECIMAL(20,2) | 成交量        |
| amount        | DECIMAL(20,4) | 成交额        |
| source        | STRING        | 数据源        |
| ingest_batch_id | STRING      | 批次号        |
| updated_at    | DATETIME      | 更新时间      |

---

### 2.3 `ods_index_daily`

结构与 `ods_daily_bar` 类似，只是主键为 `index_id, trade_date`，`index_id` 可复用 `dim_security.security_id` 中 `security_type='index'` 的记录。

---

### 2.4 `ods_financial_statement`

- **联合主键**：`security_id`, `report_period`, `statement_type`

| 字段名          | 类型          | 说明                             |
|-----------------|---------------|----------------------------------|
| security_id     | STRING        | 证券ID                           |
| report_period   | DATE          | 报告期末日                       |
| announce_date   | DATE          | 公告日                           |
| statement_type  | STRING        | IS/BS/CF/ALL                     |
| fiscal_year     | INT           | 会计年度                         |
| fiscal_quarter  | INT           | 季度（1/2/3/4）                  |
| total_revenue   | DECIMAL(20,4) | 营业总收入                       |
| net_profit      | DECIMAL(20,4) | 归母净利润                       |
| total_assets    | DECIMAL(20,4) | 总资产                           |
| total_liabilities | DECIMAL(20,4) | 总负债                         |
| operating_cashflow | DECIMAL(20,4) | 经营活动现金流量净额          |
| roe             | DECIMAL(10,4) | 净资产收益率                     |
| gross_margin    | DECIMAL(10,4) | 毛利率                           |
| eps             | DECIMAL(10,4) | 每股收益                         |
| net_profit_yoy  | DECIMAL(10,4) | 净利润同比增速                   |
| source          | STRING        | tushare                          |
| ingest_batch_id | STRING        | 批次号                           |
| updated_at      | DATETIME      | 更新时间                         |

---

### 2.5 `ods_corporate_action`

- **联合主键**：`security_id`, `ex_date`, `action_type`

| 字段名         | 类型          | 说明                     |
|----------------|---------------|--------------------------|
| security_id    | STRING        | 证券ID                   |
| ex_date        | DATE          | 除权除息日期             |
| action_type    | STRING        | dividend/split/rights 等 |
| cash_dividend  | DECIMAL(18,4) | 每股现金分红             |
| bonus_share_ratio | DECIMAL(10,4) | 送股比例             |
| rights_issue_ratio| DECIMAL(10,4) | 配股比例             |
| rights_issue_price| DECIMAL(18,4) | 配股价格             |
| source         | STRING        | tushare/other            |
| ingest_batch_id| STRING        | 批次号                   |
| updated_at     | DATETIME      | 更新时间                 |

---

## 3. 账户与交易（QMT 主）

### 3.1 `ods_account_info`

| 字段名      | 类型    | 说明                     |
|-------------|---------|--------------------------|
| account_id  | STRING  | 账户ID（主键）          |
| broker      | STRING  | 券商名称                 |
| market_scope| STRING  | CN/HK/CN+HK             |
| currency    | STRING  | 货币                     |
| created_at  | DATETIME| 创建时间                 |
| updated_at  | DATETIME| 更新时间                 |

---

### 3.2 `ods_account_equity_daily`

- **联合主键**：`account_id`, `trade_date`

| 字段名        | 类型          | 说明                        |
|---------------|---------------|-----------------------------|
| account_id    | STRING        | 账户ID                      |
| trade_date    | DATE          | 交易日                      |
| total_equity  | DECIMAL(20,4) | 总资产                      |
| cash          | DECIMAL(20,4) | 现金                        |
| frozen_cash   | DECIMAL(20,4) | 冻结资金                    |
| market_value  | DECIMAL(20,4) | 市值                        |
| available_funds | DECIMAL(20,4) | 可用资金                  |
| leverage_ratio| DECIMAL(10,4) | 杠杆倍数（如适用）          |
| source        | STRING        | qmt                         |
| ingest_batch_id | STRING      | 批次号                      |
| updated_at    | DATETIME      | 更新时间                    |

---

### 3.3 `ods_position_snapshot`

- **联合主键**：`account_id`, `security_id`, `snapshot_time`

| 字段名        | 类型          | 说明                          |
|---------------|---------------|-------------------------------|
| account_id    | STRING        | 账户ID                        |
| security_id   | STRING        | 证券ID                        |
| snapshot_time | DATETIME      | 快照时间（建议日终统一时刻） |
| quantity      | DECIMAL(20,4) | 持仓数量                      |
| available_qty | DECIMAL(20,4) | 可用数量                      |
| avg_cost      | DECIMAL(18,4) | 成本价                        |
| market_price  | DECIMAL(18,4) | 市价                          |
| market_value  | DECIMAL(20,4) | 市值                          |
| unrealized_pnl| DECIMAL(20,4) | 浮动盈亏                      |
| realized_pnl_daily | DECIMAL(20,4) | 当日已实现盈亏           |
| source        | STRING        | qmt                           |
| ingest_batch_id | STRING      | 批次号                        |
| updated_at    | DATETIME      | 更新时间                      |

---

### 3.4 `ods_order`

- **主键**：`order_id`

| 字段名      | 类型          | 说明                     |
|-------------|---------------|--------------------------|
| order_id    | STRING        | 订单ID                   |
| account_id  | STRING        | 账户ID                   |
| strategy_id | STRING        | 关联策略ID（可为空）     |
| security_id | STRING        | 证券ID                   |
| order_time  | DATETIME      | 委托时间                 |
| side        | STRING        | buy/sell 等              |
| order_type  | STRING        | limit/market 等          |
| price       | DECIMAL(18,4) | 委托价                   |
| quantity    | DECIMAL(20,4) | 委托数量                 |
| status      | STRING        | new/filled/cancelled 等 |
| source      | STRING        | qmt/manual               |
| ingest_batch_id | STRING    | 批次号                   |
| updated_at  | DATETIME      | 更新时间                 |

---

### 3.5 `ods_trade`

- **主键**：`trade_id`

| 字段名      | 类型          | 说明                          |
|-------------|---------------|-------------------------------|
| trade_id    | STRING        | 成交ID                        |
| order_id    | STRING        | 对应订单ID                    |
| account_id  | STRING        | 账户ID                        |
| security_id | STRING        | 证券ID                        |
| trade_time  | DATETIME      | 成交时间                      |
| side        | STRING        | buy/sell 等                   |
| price       | DECIMAL(18,4) | 成交价                        |
| quantity    | DECIMAL(20,4) | 成交数量                      |
| amount      | DECIMAL(20,4) | 成交金额                      |
| fee         | DECIMAL(18,4) | 手续费                        |
| tax         | DECIMAL(18,4) | 税费                          |
| source      | STRING        | qmt                           |
| ingest_batch_id | STRING    | 批次号                        |
| updated_at  | DATETIME      | 更新时间                      |

---

## 4. 因子与策略相关实体

### 4.1 `dwd_factor_value`

- **联合主键**：`security_id`, `trade_date`, `factor_id`

| 字段名      | 类型          | 说明                        |
|-------------|---------------|-----------------------------|
| security_id | STRING        | 证券ID                      |
| trade_date  | DATE          | 计算日期/生效日期           |
| factor_id   | STRING        | 因子ID                      |
| factor_value| DECIMAL(20,6) | 因子值                      |
| value_type  | STRING        | raw/zscore/rank 等         |
| calc_version| STRING        | 计算版本                    |
| source      | STRING        | 计算服务名                  |
| updated_at  | DATETIME      | 更新时间                    |

---

### 4.2 `dm_strategy_signal`

- **联合主键**：`strategy_id`, `security_id`, `signal_time`, `signal_type`

| 字段名        | 类型          | 说明                              |
|---------------|---------------|-----------------------------------|
| strategy_id   | STRING        | 策略ID                            |
| security_id   | STRING        | 证券ID（组合级信号可为空）       |
| signal_time   | DATETIME      | 信号生成时间                      |
| signal_type   | STRING        | open/add/reduce/close/...        |
| direction     | STRING        | long/short                        |
| target_weight | DECIMAL(10,4) | 目标权重（相对策略资产）          |
| price_hint_min| DECIMAL(18,4) | 建议价格下界                      |
| price_hint_max| DECIMAL(18,4) | 建议价格上界                      |
| valid_from    | DATETIME      | 有效期开始                        |
| valid_to      | DATETIME      | 有效期结束                        |
| comment       | STRING        | 备注说明                          |
| source        | STRING        | backtest/live                     |
| created_at    | DATETIME      | 创建时间                          |

---

## 5. 用户/订阅/支付相关（与 BRD 对齐）

这里只定义与量化平台核心紧耦合的业务表，支付/用户体系可进一步细化。

### 5.1 `dim_user`

| 字段名      | 类型     | 说明                               |
|-------------|----------|------------------------------------|
| user_id     | STRING   | 用户ID（主键）                    |
| mobile      | STRING   | 手机号                             |
| email       | STRING   | 邮箱                               |
| password_hash | STRING | 密码哈希                           |
| role        | STRING   | user/power_user/admin             |
| risk_profile| STRING   | 风险偏好标签                       |
| created_at  | DATETIME | 注册时间                           |
| updated_at  | DATETIME | 更新时间                           |

### 5.2 `subscription`

| 字段名        | 类型     | 说明                           |
|---------------|----------|--------------------------------|
| subscription_id | STRING | 主键                           |
| user_id       | STRING   | 用户ID                         |
| strategy_id   | STRING   | 策略ID                         |
| start_date    | DATE     | 生效日期                       |
| end_date      | DATE     | 失效日期                       |
| plan_type     | STRING   | month/quarter/year 等         |
| status        | STRING   | active/expired/cancelled      |
| created_at    | DATETIME | 创建时间                       |
| updated_at    | DATETIME | 更新时间                       |

### 5.3 `order_payment`

| 字段名      | 类型     | 说明                             |
|-------------|----------|----------------------------------|
| order_id    | STRING   | 订单ID（主键）                  |
| user_id     | STRING   | 用户ID                           |
| strategy_id | STRING   | 策略ID                           |
| amount      | DECIMAL(18,4) | 金额                        |
| currency    | STRING   | 货币（CNY）                     |
| channel     | STRING   | wechatpay/alipay                |
| status      | STRING   | pending/paid/failed/refunded    |
| created_at  | DATETIME | 创建时间                         |
| paid_at     | DATETIME | 支付成功时间（可空）            |
| updated_at  | DATETIME | 更新时间                         |

---

## 6. 契约使用说明

- 后端服务与 ETL 任务必须遵守以上字段定义和主键规则。
- 新增字段时：
  - 必须更新本文件与 `tables.yml` 配置；
  - 保持对现有读取逻辑的向后兼容（增加非必填字段优先）。
- 若未来接入新的数据源（如 Wind、另一个券商），推荐：
  - 新源数据先落 `raw_*` 表；
  - 在 ODS 层使用同一字段命名与类型，与现有契约对齐。

