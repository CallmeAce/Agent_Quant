## Openclaw QuantOps Agent 用例拆解

本文件对应 todo「将Openclaw Agent的任务编排、告警与报表场景拆解为可执行的用例列表」。

---

## 1. 角色与总体职责

Agent 作为“量化运维大脑”，负责：

- 定时调度：交易日内外的 ETL、因子、策略与信号任务。
- 运行监控：任务成功率、耗时、结果规模（记录数）等。
- 异常告警：任务失败、数据缺失、策略结果异常。
- 报表生成：针对策略表现和系统健康的日报/周报。

---

## 2. 任务编排（DAG 视角）

### 2.1 每日 T0 收盘后任务流

1. `job_trade_calendar_check`
   - 输入：日期 `T0`。
   - 行为：确认 `T0` 是否为交易日，不是则记录并终止后续任务链。
2. `job_tushare_daily_bar(T0)`
   - 拉取 T0 日线行情 → 写入 `ods_daily_bar`。
3. `job_tushare_financials_if_needed(T0)`
   - 若为特定财报窗口/定期任务，则更新 `ods_financial_statement`。
4. `job_qmt_daily_positions(T0)`
   - 从 QMT 拉取日终账户/持仓/成交 → 写入 `ods_account_equity_daily`, `ods_position_snapshot`, `ods_trade`。
5. `job_factor_daily(T0)`
   - 从 ODS/DWD 读取行情与财报 → 计算因子 → 写入 `dwd_factor_value`。
6. `job_strategy_stock_selection(T0)`
   - 对开启的策略运行选股与调仓逻辑 → 存储策略级持仓/信号（如 `dm_strategy_signal` / `dwd_strategy_position`）。

上述任务具有依赖关系：
- `factor_daily` 依赖 `tushare_daily_bar`（和可选财报）；
- `strategy_stock_selection` 依赖 `factor_daily` 完成。

### 2.2 每日 T+1 开盘前/盘中任务流

1. `job_market_open_health_check(T1)`
   - 检查行情源可用性（QMT / Tushare）、数据库连接等。
2. `job_realtime_signal_generation(T1, session=AM/PM)`
   - 基于前一日选股结果 + 实时价格/账户情况生成买卖点信号。
   - 写入 `dm_strategy_signal`（live）。
3. `job_push_signals_to_users(T1, session=AM/PM)`
   - 读取新生成的信号 + 用户 `subscription` 列表。
   - 按策略/用户维度推送 Telegram/邮件信息，记录 `NotificationLog`。

### 2.3 审计与对账任务（每日/每周）

- `job_notification_delivery_audit`
  - 检查信号生成条数与通知发送条数是否匹配。
- `job_payment_reconciliation`
  - 对账支付渠道流水与本地 `order_payment` / `subscription` 数据。

---

## 3. 监控与告警用例

### 3.1 任务级监控

对每个 Job 记录：
- 开始/结束时间
- 状态：成功/失败/部分成功
- 处理记录数：输入条数、输出条数
- 错误计数：校验失败条数

当出现以下情况之一时，Agent 触发告警：
- Job 超时（超过预设 SLA）。
- Job 失败或连续多次重试失败。
- 输出记录数异常（例如历史均值±3 标准差之外，或直接为 0）。

### 3.2 数据质量告警

针对关键表：
- `ods_daily_bar`：当日记录数显著低于最近 N 日均值；关键指数缺失数据。
- `dwd_factor_value`：新因子值全为 NULL/0；数量与 `dim_security` 对不上。
- `dm_strategy_signal`：开启中的策略某日无任何选股/信号（不符合策略设定）。

告警内容示例：
- 标题：`[CRITICAL] T0 Daily Bar Missing for SSE 2025-02-20`
- 内容：包含 Job 名称、批次号、错误摘要、快速排查链接（日志位置等）。

---

## 4. 报表生成用例

### 4.1 每日策略运行日报（可先以邮件/Markdown 形式输出）

内容包括：
- 策略层面：
  - 当日收益、当日调仓次数、是否有异常回撤。
  - 是否按计划生成信号（是/否，异常原因）。
- 任务层面：
  - ETL/因子/策略/通知各 Job 的执行结果统计。
  - 失败/重试次数。

由 Agent 汇总相关表（`ods_account_equity_daily`, `dm_strategy_signal`, `etl_job_metrics`），生成简单报告，发送给管理员。

### 4.2 每周/每月策略评估报告

内容包括：
- 策略表现排名（收益、回撤、夏普）。
- 新增/流失订阅用户数。
- 建议运营动作（如“某策略近 3 个月表现偏弱，建议降价或提示风险”）。

可初期仅生成数据明细供人工分析，后续再自动化生成图文报告。

---

## 5. 配置与扩展

### 5.1 任务配置

使用配置文件（如 `agent_jobs.yml`）描述：
- Job 名称、入口函数（Python 模块路径）。
- 调度表达式（CRON）。
- 依赖关系（前置 Job 列表）。
- 超时时间与重试策略。

### 5.2 告警通道与等级

- 通道：Telegram / 邮件，未来可扩展企业微信/钉钉。
- 等级：INFO / WARNING / CRITICAL。
- 不同等级对应不同通知策略（如 CRITICAL 需要所有管理员都收到）。

---

## 6. 后续可扩展用例

- 因子体检任务：定期回测单因子表现，自动标记“疑似失效”的因子。
- 策略风格漂移监控：监控策略持仓的行业/市值/风格暴露变化，偏离预期区间时告警。
- 资源使用监控：监控回测任务 CPU/内存/数据库负载，防止高并发影响线上服务。

