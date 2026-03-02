# Tushare Pro API 快速参考

**最后更新:** 2026-03-05  
**数据来源:** https://tushare.pro/document/2

---

## 📊 核心接口字段对照表

### 1. daily - 日线行情

**接口:** `pro.daily(ts_code='', trade_date='', start_date='', end_date='')`

**输入参数:**
```
ts_code      str  N  股票代码（支持多个，逗号分隔）
trade_date   str  N  交易日期 (YYYYMMDD)
start_date   str  N  开始日期
end_date     str  N  结束日期
```

**输出字段:**
```
ts_code      str   股票代码
trade_date   str   交易日期
open         float 开盘价
high         float 最高价
low          float 最低价
close        float 收盘价
pre_close    float 昨收价【除权价】
change       float 涨跌额
pct_chg      float 涨跌幅【(今收 - 除权昨收)/除权昨收】
vol          float 成交量（手）
amount       float 成交额（千元）
```

**更新频率:** 交易日 15:00-16:00  
**积分消耗:** 1 次/6000 条

---

### 2. daily_basic - 每日指标 ⭐ 重要

**接口:** `pro.daily_basic(ts_code='', trade_date='', start_date='', end_date='')`

**输入参数:**
```
ts_code      str  Y  股票代码（二选一）
trade_date   str  N  交易日期（二选一）
start_date   str  N  开始日期
end_date     str  N  结束日期
```

**输出字段 (核心因子来源):**
```
ts_code          str   TS 股票代码
trade_date       str   交易日期
close            float 当日收盘价
turnover_rate    float 换手率（%）
turnover_rate_f  float 换手率（自由流通股）
volume_ratio     float 量比
pe               float 市盈率（总市值/净利润，亏损为空）
pe_ttm           float 市盈率（TTM，亏损为空）⭐
pb               float 市净率（总市值/净资产）⭐
ps               float 市销率
ps_ttm           float 市销率（TTM）⭐
dv_ratio         float 股息率（%）
dv_ttm           float 股息率（TTM）（%）
total_share      float 总股本（万股）
float_share      float 流通股本（万股）
free_share       float 自由流通股本（万）
total_mv         float 总市值（万元）⭐
circ_mv          float 流通市值（万元）
```

**更新频率:** 交易日 15:00-16:00  
**积分消耗:** 1 次/5000 条  
**重要性:** ⭐⭐⭐⭐⭐ (包含 PE/PB/PS 等核心估值因子)

---

### 3. fina_indicator - 财务指标 ⭐ 重要

**接口:** `pro.fina_indicator(ts_code='', ann_date='', start_date='', end_date='', period='')`

**输入参数:**
```
ts_code      str  Y  TS 股票代码
ann_date     str  N  公告日期
start_date   str  N  报告期开始日期
end_date     str  N  报告期结束日期
period       str  N  报告期 (如 20171231 表示年报)
```

**输出字段 (核心因子来源):**
```
ts_code            str   TS 代码
ann_date           str   公告日期
end_date           str   报告期
eps                float 基本每股收益
dt_eps             float 稀释每股收益
total_revenue_ps   float 每股营业总收入
revenue_ps         float 每股营业收入
capital_rese_ps    float 每股资本公积
surplus_rese_ps    float 每股盈余公积
undist_profit_ps   float 每股未分配利润
extra_item         float 非经常性损益
profit_dedt        float 扣除非经常性损益后的净利润
gross_margin       float 毛利率 (%) ⭐
current_ratio      float 流动比率
quick_ratio        float 速动比率
cash_ratio         float 保守速动比率
invturn_days       float 存货周转天数
arturn_days        float 应收账款周转天数
inv_turn           float 存货周转率
ar_turn            float 应收账款周转率
ca_turn            float 流动资产周转率
fa_turn            float 固定资产周转率
assets_turn        float 总资产周转率
op_income          float 经营活动净收益
valuechange_income float 价值变动净收益
```

**续表 (利润表相关):**
```
total_revenue      float 营业总收入
revenue            float 营业收入
int_income         float 利息收入
prem_earned        float 已赚保费
comm_income        float 手续费及佣金收入
n_commis_income    float 手续费及佣金净收入
n_oth_income       float 其他经营净收益
n_oth_b_income     float 加:其他业务净收益
prem_income        float 保险业务收入
out_prem           float 减：分出保费
```

**更新频率:** 季度（财报披露后）  
**积分消耗:** 1 次/5000 条  
**重要性:** ⭐⭐⭐⭐⭐ (包含 ROE、毛利率等质量因子)

---

### 4. stock_basic - 股票列表

**接口:** `pro.stock_basic(exchange='', list_status='', fields='')`

**输入参数:**
```
ts_code        str  N  TS 股票代码
name           str  N  名称
market         str  N  市场类别（主板/创业板/科创板/CDR/北交所）
list_status    str  N  上市状态 L 上市 D 退市 P 暂停上市 G 过会未交易
exchange       str  N  交易所 SSE/SZSE/BSE
is_hs          str  N  是否沪深港通标的 N 否 H 沪股通 S 深股通
```

**输出字段:**
```
ts_code        str   TS 代码
symbol         str   股票代码（纯数字）
name           str   股票名称
area           str   地域
industry       str   所属行业
fullname       str   股票全称
enname         str   英文全称
cnspell        str   拼音缩写
market         str   市场类型
exchange       str   交易所代码
curr_type      str   交易货币
list_status    str   上市状态 L 上市 D 退市 P 暂停上市
list_date      str   上市日期
delist_date    str   退市日期
```

**更新频率:** 每周（变化少）  
**积分消耗:** 1 次/全部股票

---

### 5. trade_cal - 交易日历

**接口:** `pro.trade_cal(exchange='', start_date='', end_date='', is_open='')`

**输入参数:**
```
exchange     str  N  交易所 SSE/SZSE/CFFEX/SHFE/CZCE/DCE/INE
start_date   str  N  开始日期 (YYYYMMDD)
end_date     str  N  结束日期
is_open      str  N  是否交易 '0'休市 '1'交易
```

**输出字段:**
```
exchange       str   交易所 SSE/SZSE
cal_date       str   日历日期
is_open        str   是否交易 0 休市 1 交易
pretrade_date  str   上一个交易日
```

**更新频率:** 每年（年初）  
**积分消耗:** 1 次/全年

---

### 6. income - 利润表

**接口:** `pro.income(ts_code='', ann_date='', start_date='', end_date='', period='')`

**输入参数:**
```
ts_code      str  Y  股票代码
ann_date     str  N  公告日期
start_date   str  N  公告日开始日期
end_date     str  N  公告日结束日期
period       str  N  报告期
report_type  str  N  报告类型
comp_type    str  N  公司类型 (1 一般工商业 2 银行 3 保险 4 证券)
```

**输出字段 (部分):**
```
ts_code            str   TS 代码
ann_date           str   公告日期
f_ann_date         str   实际公告日期
end_date           str   报告期
report_type        str   报告类型
comp_type          str   公司类型
end_type           str   报告期类型
basic_eps          float 基本每股收益
diluted_eps        float 稀释每股收益
total_revenue      float 营业总收入
revenue            float 营业收入
net_profit         float 净利润
net_profit_atmp    float 归属于母公司所有者的净利润 ⭐
op_income          float 营业利润
total_profit       float 利润总额
```

**更新频率:** 季度  
**积分消耗:** 1 次/5000 条

---

## 🎯 因子计算数据源映射

### 估值因子 (Valuation)

| 因子 | 数据源 | 计算方式 |
|------|--------|----------|
| PE_TTM | daily_basic.pe_ttm | 直接使用 |
| PB | daily_basic.pb | 直接使用 |
| PS_TTM | daily_basic.ps_ttm | 直接使用 |
|总市值 | daily_basic.total_mv | 直接使用（万元） |

### 质量因子 (Quality)

| 因子 | 数据源 | 计算方式 |
|------|--------|----------|
| ROE | fina_indicator | 需计算或从利润表推导 |
| 毛利率 | fina_indicator.gross_margin | 直接使用（%） |
| 净利率 | fina_indicator | net_profit / total_revenue |
| 流动比率 | fina_indicator.current_ratio | 直接使用 |
| 速动比率 | fina_indicator.quick_ratio | 直接使用 |

### 成长因子 (Growth)

| 因子 | 数据源 | 计算方式 |
|------|--------|----------|
| 营收增速 | income | (本期 revenue - 同期) / 同期 |
| 净利润增速 | income | (本期 net_profit - 同期) / 同期 |

### 动量因子 (Momentum)

| 因子 | 数据源 | 计算方式 |
|------|--------|----------|
| 20 日动量 | daily.close | (close - close_20d_ago) / close_20d_ago |
| 60 日动量 | daily.close | (close - close_60d_ago) / close_60d_ago |

### 流动性因子 (Liquidity)

| 因子 | 数据源 | 计算方式 |
|------|--------|----------|
| 换手率 | daily_basic.turnover_rate | 直接使用（%） |
| 量比 | daily_basic.volume_ratio | 直接使用 |
| 日均成交额 | daily.amount | 20 日平均 |

---

## 📋 阶段一数据拉取计划 (CN_VALUE_MID_V1)

### P0 核心数据

| 数据 | 接口 | 频率 | 时间 | 积分/次 |
|------|------|------|------|---------|
| 全市场日线 | daily | 每日 | 16:00 后 | ~5 次 |
| 全市场每日指标 | daily_basic | 每日 | 16:00 后 | ~5 次 |
| 股票列表 | stock_basic | 每周 | 周一 | 1 次 |
| 交易日历 | trade_cal | 每年 | 年初 | 1 次 |

### P1 财务数据

| 数据 | 接口 | 频率 | 时间 | 积分/次 |
|------|------|------|------|---------|
| 财务指标 | fina_indicator | 季度 | 财报季后 | ~10 次 |
| 利润表 | income | 季度 | 财报季后 | ~10 次 |

**积分预算:** 基础积分 (~100 分/月) 足够覆盖阶段一需求

---

## ⚠️ 注意事项

### 1. 数据质量
- **停牌股票:** daily 接口不提供停牌期间数据
- **亏损股票:** PE 字段为空，需要特殊处理
- **新股:** 上市初期数据可能不稳定

### 2. 字段说明
- **成交量单位:** 手（1 手=100 股）
- **成交额单位:** 千元
- **市值单位:** 万元
- **百分比字段:** 部分为百分数（如 5.5 表示 5.5%），部分为小数（如 0.055）

### 3. 复权处理
```python
# 使用 adj_factor 计算复权价格
adj_close = close * adj_factor / adj_factor_base
```

### 4. 代码格式
- **股票代码:** `000001.SZ` (6 位数字。交易所后缀)
- **日期格式:** `20260305` (YYYYMMDD 字符串)

---

## 🔗 相关文档

- [Tushare 官网](https://tushare.pro)
- [积分规则](https://tushare.pro/weborder/#/point)
- [数据工具](https://tushare.pro/webclient)
- [项目数据契约](./data_contracts.md)

