## 因子池与策略池设计（可扩展、易复用）

本文件对应 todo「因子池，策略池的设计，满足可扩展，方便调用」。

---

## 1. 总体设计原则

- **解耦**：因子计算逻辑与策略逻辑解耦，因子以“标准接口 + 元数据配置”形式提供。
- **可扩展**：新增一个因子或策略，不影响已有因子/策略，只需：
  - 注册元数据（因子ID/策略ID + 描述）
  - 增加一个实现模块或配置文件。
- **统一存储**：所有因子结果落地到 `dwd_factor_value`，所有策略信号落地到 `dm_strategy_signal`。
- **版本化**：因子和策略均支持版本号，便于回测与线上策略共存。

---

## 2. 因子池设计

### 2.1 因子元数据表（dim_factor，逻辑设计）

- `factor_id`：唯一ID（例：`PE_TTM`, `MOM_20D`）。
- `name`：中文名称。
- `category`：类别（valuation / growth / quality / momentum / volatility / liquidity / risk）。
- `description`：计算逻辑简述。
- `universe`：适用标的池（A股/港股/指数等）。
- `update_freq`：更新频率（daily/monthly/quarterly）。
- `source_tables`：依赖的数据表（例如：`ods_daily_bar`, `ods_financial_statement`）。
- `formula_reference`：计算公式说明文档链接或代码模块路径。
- `status`：active/deprecated。

> 该表可以作为管理端“因子列表”的基础。

### 2.2 因子实现接口（Factor Engine 抽象）

建议在代码中统一约定一个接口，例如 Python 伪代码：

```python
class Factor:
    def __init__(self, factor_id: str, config: dict):
        self.factor_id = factor_id
        self.config = config

    def load_raw_data(self, start_date, end_date):
        """从 ODS/DWD 读取计算该因子所需数据。"""
        raise NotImplementedError

    def compute(self, raw_df):
        """返回包含 security_id, trade_date, factor_value 的 DataFrame。"""
        raise NotImplementedError
```

新增因子时：
- 在 `dim_factor` 中注册元数据；
- 在因子库目录（如 `factors/valuation/pe_ttm.py`）中实现上述接口；
- 在因子计算管线配置（如 `factor_pipeline.yml`）中引用该因子ID，即可被批量任务自动调用。

### 2.3 因子分类与首批因子池

- **估值类（valuation）**
  - `PE_TTM`：滚动市盈率。
  - `PB`：市净率。
  - `PS_TTM`：滚动市销率。
  - `EV_EBITDA`：企业价值/EBITDA（可后续扩展）。
- **成长类（growth）**
  - `REV_GROWTH_YOY`：营业收入同比增速。
  - `REV_GROWTH_3Y`：三年复合收入增速。
  - `NP_GROWTH_YOY`：净利润同比增速。
- **质量类（quality）**
  - `ROE`：净资产收益率。
  - `ROA`：资产收益率。
  - `GROSS_MARGIN`：毛利率。
  - `OPER_CF_TO_NP`：经营现金流/净利润。
- **动量类（momentum）**
  - `MOM_20D`, `MOM_60D`, `MOM_120D`：不同期限的价格动量。
  - `VOL_MOM_20D`：成交量动量。
- **波动与风险（volatility/risk）**
  - `VOLATILITY_20D`, `VOLATILITY_120D`：年化波动率。
  - `MAX_DRAWDOWN_120D`：过去 120 日最大回撤。
- **流动性（liquidity）**
  - `TURNOVER_20D`：20 日平均换手率。
  - `AMOUNT_20D`：20 日平均成交额。

所有这些因子计算结果统一写入 `dwd_factor_value`，通过 `(security_id, trade_date, factor_id)` 三元组索引。

---

## 3. 策略池设计

### 3.1 策略元数据表（dim_strategy，逻辑设计）

- `strategy_id`：唯一ID（如 `CN_VALUE_MID_V1`）。
- `name`：中文名称。
- `style_tags`：标签列表（['value', 'midterm']）。
- `market`：适用市场（CN/HK/CN+HK）。
- `universe_rule_ref`：标的池规则引用（可指向配置文件或代码模块）。
- `factor_set`：该策略使用的主要因子ID列表。
- `rebalance_freq`：调仓频率（daily/weekly/monthly）。
- `target_holding_period`：目标持有期。
- `risk_constraints_ref`：风险约束配置引用。
- `status`：草稿/内测/公开/下线。

### 3.2 策略实现接口（Strategy Engine 抽象）

策略逻辑同样通过接口解耦：

```python
class Strategy:
    def __init__(self, strategy_id: str, config: dict):
        self.strategy_id = strategy_id
        self.config = config

    def load_universe(self, trade_date):
        """根据 universe_rule_ref 和市场信息加载可选标的池。"""
        raise NotImplementedError

    def load_factors(self, trade_date):
        """从 dwd_factor_value 中读取相关因子值。"""
        raise NotImplementedError

    def generate_signals(self, trade_date):
        """输出选股/调仓信号，写入 dm_strategy_signal。"""
        raise NotImplementedError
```

策略引擎根据 `dim_strategy` & 配置文件动态实例化对应策略类。

---

## 4. 策略调用与前端展示的衔接

- 策略引擎在 T0 与 T+1 生成的信号，写入 `dm_strategy_signal`。
- Backtest/Live 运行结果（净值曲线、持仓等）统一写入策略级别的事实表（如 `dwd_strategy_nav`、`dwd_strategy_position`，可后续扩展）。
- 前端：
  - “策略广场”从 `dim_strategy` + 聚合后的绩效表读取展示信息。
  - 单策略详情页从 `dwd_strategy_nav` / `dm_strategy_signal` 拉取净值曲线和信号列表。

---

## 5. 扩展新因子/策略的步骤（操作视角）

### 5.1 新增因子

1. 在 `dim_factor` 表中登记元数据。
2. 在因子代码库中新增实现类，继承 `Factor` 接口。
3. 在 `factor_pipeline.yml` 中添加该因子配置（更新频率、依赖表、计算参数）。
4. 在定时任务中增加/修改对应因子任务（或复用统一管线）。

### 5.2 新增策略

1. 在 `dim_strategy` 表中登记策略元数据（ID、风格、因子集合、约束等）。
2. 在策略代码库中实现 `Strategy` 接口。
3. 配置策略回测任务（BacktestService），验证表现。
4. 管理员在后台审核并切换状态为“公开”，策略引擎纳入生产调度。

