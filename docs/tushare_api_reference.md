# Tushare Pro API 参考文档

**最后更新:** 2026-03-05  
**来源:** https://tushare.pro/document/2

---

## 📊 核心接口汇总

### 1. 日线行情 (daily)

**接口名:** `pro.daily()`  
**文档:** https://tushare.pro/document/2?doc_id=27

**输入参数:**
| 参数 | 类型 | 必选 | 描述 |
|------|------|------|------|
| ts_code | str | N | 股票代码（支持多个，逗号分隔） |
| trade_date | str | N | 交易日期 (YYYYMMDD) |
| start_date | str | N | 开始日期 (YYYYMMDD) |
| end_date | str | N | 结束日期 (YYYYMMDD) |

**输出字段:**
| 字段 | 类型 | 描述 |
|------|------|------|
| ts_code | str | 股票代码 |
| trade_date | str | 交易日期 |
| open | float | 开盘价 |
| high | float | 最高价 |
| low | float | 最低价 |
| close | float | 收盘价 |
| pre_close | float | 昨收价（除权价） |
| change | float | 涨跌额 |
| pct_change | float | 涨跌幅（%） |
| vol | float | 成交量（手） |
| amount | float | 成交额（千元） |

**调取限制:** 
- 基础积分：每分钟 500 次，每次 6000 条
- 一次请求相当于提取一个股票 23 年历史

**注意:** 交易日每天 15 点～16 点入库，未复权行情，停牌期间不提供数据

---

### 2. 财务指标 (fina_indicator)

**接口名:** `pro.fina_indicator()`  
**文档:** https://tushare.pro/document/2?doc_id=79

**输入参数:**
| 参数 | 类型 | 必选 | 描述 |
|------|------|------|------|
| ts_code | str | Y | TS 股票代码 |
| ann_date | str | N | 公告日期 |
| start_date | str | N | 报告期开始日期 |
| end_date | str | N | 报告期结束日期 |
| period | str | N | 报告期 (如 20171231 表示年报) |

**输出字段 (核心):**
| 字段 | 类型 | 描述 |
|------|------|------|
| ts_code | str | TS 代码 |
| ann_date | str | 公告日期 |
| end_date | str | 报告期 |
| eps | float | 基本每股收益 |
| dt_eps | float | 稀释每股收益 |
| total_revenue_ps | float | 每股营业总收入 |
| revenue_ps | float | 每股营业收入 |
| roe | float | 净资产收益率 (%) |
| roa | float | 总资产净利润率 (%) |
| gross_margin | float | 毛利率 (%) |
| net_profit_margin | float | 净利率 (%) |

---

### 3. 每日指标 (daily_basic)

**接口名:** `pro.daily_basic()`  
**文档:** https://tushare.pro/document/2?doc_id=32

**输入参数:**
| 参数 | 类型 | 必选 | 描述 |
|------|------|------|------|
| ts_code | str | Y | 股票代码（二选一） |
| trade_date | str | N | 交易日期（二选一） |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |

**输出字段 (核心):**
| 字段 | 类型 | 描述 |
|------|------|------|
| ts_code | str | TS 股票代码 |
| trade_date | str | 交易日期 |
| close | float | 当日收盘价 |
| turnover_rate | float | 换手率（%） |
| turnover_rate_f | float | 换手率（自由流通股） |
| volume_ratio | float | 量比 |
| pe | float | 市盈率（总市值/净利润） |
| pe_ttm | float | 市盈率（TTM） |
| pb | float | 市净率 |
| ps | float | 市销率 |
| ps_ttm | float | 市销率（TTM） |
| dv_ratio | float | 股息率（%） |
| total_mv | float | 总市值（元） |
| circ_mv | float | 流通市值（元） |

---

### 4. 交易日历 (trade_cal)

**接口名:** `pro.trade_cal()`  
**文档:** https://tushare.pro/document/2?doc_id=26

**输入参数:**
| 参数 | 类型 | 必选 | 描述 |
|------|------|------|------|
| exchange | str | N | 交易所 (SSE/SZSE) |
| start_date | str | N | 开始日期 (YYYYMMDD) |
| end_date | str | N | 结束日期 (YYYYMMDD) |
| is_open | str | N | 是否交易 ('0'休市 '1'交易) |

**输出字段:**
| 字段 | 类型 | 描述 |
|------|------|------|
| exchange | str | 交易所 |
| cal_date | str | 日历日期 |
| is_open | str | 是否交易 (0/1) |
| pretrade_date | str | 上一交易日 |

---

### 5. 股票列表 (stock_basic)

**接口名:** `pro.stock_basic()`  
**文档:** https://tushare.pro/document/2?doc_id=25

**输入参数:**
| 参数 | 类型 | 必选 | 描述 |
|------|------|------|------|
| exchange | str | N | 交易所 (SSE/SZSE/BSE) |
| list_status | str | N | 上市状态 (L 上市/D 退市/P 暂停) |
| fields | str | N | 返回字段列表 |

**输出字段:**
| 字段 | 类型 | 描述 |
|------|------|------|
| ts_code | str | TS 股票代码 |
| symbol | str | 股票代码（纯数字） |
| name | str | 股票名称 |
| area | str | 地域 |
| industry | str | 所属行业 |
| list_date | str | 上市日期 |

---

## 💡 使用建议

### 1. 数据拉取策略

```python
# ✅ 推荐：按日期批量拉取
df = pro.daily(trade_date='20260305')

# ✅ 推荐：单只股票历史数据
df = pro.daily(ts_code='000001.SZ', start_date='20250101', end_date='20251231')

# ❌ 避免：一次性拉取太多股票
# 建议分批，每批 50-100 只股票
```

### 2. 积分优化

| 操作 | 积分消耗 | 建议 |
|------|----------|------|
| 日线行情 | 1 次/6000 条 | 按日期全市场拉取最划算 |
| 财务指标 | 1 次/5000 条 | 季度更新，不需要每日拉取 |
| 每日指标 | 1 次/5000 条 | 包含 PE/PB 等，强烈推荐 |

### 3. 缓存策略

```python
# 日线数据：每日 16 点后更新一次
# 财务数据：季度更新（年报/季报披露期）
# 股票列表：每周检查一次（变化少）
# 交易日历：每年更新一次
```

---

## 🔗 项目集成建议

### 当前项目已有代码

```python
# etl/extractors/tushare_extractor.py
class TushareExtractor:
    def get_daily_bar(self, trade_date: date) -> pd.DataFrame:
        params = {"trade_date": trade_date.strftime("%Y%m%d")}
        df = self.pro.daily(**params)
        return df
```

### 需要补充的接口

```python
# 1. 每日指标（获取 PE/PB 等）
def get_daily_basic(self, trade_date: date) -> pd.DataFrame:
    params = {"trade_date": trade_date.strftime("%Y%m%d")}
    df = self.pro.daily_basic(**params)
    return df

# 2. 财务指标（获取 ROE 等）
def get_fina_indicator(self, ts_code: str, period: str) -> pd.DataFrame:
    params = {"ts_code": ts_code, "period": period}
    df = self.pro.fina_indicator(**params)
    return df

# 3. 交易日历
def get_trade_cal(self, exchange: str, year: int) -> pd.DataFrame:
    params = {
        "exchange": exchange,
        "start_date": f"{year}0101",
        "end_date": f"{year}1231"
    }
    df = self.pro.trade_cal(**params)
    return df

# 4. 股票列表
def get_stock_basic(self, exchange: str) -> pd.DataFrame:
    params = {"exchange": exchange, "list_status": "L"}
    df = self.pro.stock_basic(**params)
    return df
```

---

## 📋 阶段一数据需求 (CN_VALUE_MID_V1 策略)

| 数据类型 | 接口 | 更新频率 | 优先级 |
|----------|------|----------|--------|
| 日线行情 | daily | 每日 | P0 |
| 每日指标 | daily_basic | 每日 | P0 |
| 财务指标 | fina_indicator | 季度 | P0 |
| 股票列表 | stock_basic | 每周 | P0 |
| 交易日历 | trade_cal | 每年 | P0 |

---

## ⚠️ 注意事项

1. **API 限流:** 基础积分每分钟 500 次，做好重试和限流
2. **数据时间:** 日线数据 15-16 点入库，不要在盘中拉取当日数据
3. **停牌处理:** 停牌期间日线无数据，需要特殊处理
4. **复权问题:** `daily` 接口是未复权，如需复权用 `adj_factor` 字段计算
5. **代码格式:** 日期都是 YYYYMMDD 字符串，不是标准日期格式

---

## 🔗 相关文档

- [Tushare 官网](https://tushare.pro)
- [积分规则](https://tushare.pro/weborder/#/point)
- [数据工具](https://tushare.pro/webclient)
