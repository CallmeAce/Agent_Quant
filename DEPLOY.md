# Openclaw Bot Docker 部署指南

## 快速开始

### 1. 前置要求

- Docker Desktop (Windows/Mac) 或 Docker + Docker Compose (Linux)
- 至少 2GB 可用内存
- 可选：Telegram Bot Token（用于测试 bot 功能）

### 2. 配置环境变量

复制环境变量文件并编辑：

```bash
cp .env.example .env
```

**必须配置的变量：**

| 变量名 | 说明 | 获取方式 |
|--------|------|----------|
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token | 通过 @BotFather 创建 |
| `TELEGRAM_ADMIN_CHAT_ID` | 管理员 Chat ID | 通过 @userinfobot 获取 |
| `TUSHARE_TOKEN` | Tushare API Token | https://tushare.pro |
| `DATABASE_URL` | 数据库连接 URL | 默认已配置好 |

**获取 Telegram Bot Token 步骤：**

1. 在 Telegram 中搜索 @BotFather
2. 发送 `/newbot` 创建新 bot
3. 按提示输入 bot 名称和用户名
4. 保存返回的 token

**获取 Chat ID：**

1. 在 Telegram 中搜索 @userinfobot
2. 发送任意消息
3. 复制返回的 Id 值

**代理配置（如使用代理）：**

如果你使用代理访问 Telegram（如 TUN 模式），需要在 `docker-compose.yml` 中为 bot 服务添加：

```yaml
bot:
  environment:
    HTTPS_PROXY: http://host.docker.internal:<代理端口>
    HTTP_PROXY: http://host.docker.internal:<代理端口>
    NO_PROXY: db,pgadmin,api,scheduler,localhost,127.0.0.1
  extra_hosts:
    - "host.docker.internal:host-gateway"
```

常见代理端口：Clash 混合代理 `7897`，HTTP 代理 `7890`

### 3. 启动服务

**Windows:**
```bash
start.bat
```

**Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

**或者使用 Docker Compose 命令：**

```bash
# 完整部署（数据库 + Bot + API + pgAdmin）
docker compose up -d

# 最小化部署（仅数据库 + Bot）
docker compose -f docker-compose.test.yml up -d
```

### 4. 访问服务

| 服务 | 地址 | 说明 |
|------|------|------|
| API | http://localhost:8000 | FastAPI 服务 |
| API Docs | http://localhost:8000/docs | Swagger 文档 |
| pgAdmin | http://localhost:5050 | 数据库管理界面 |
| PostgreSQL | localhost:5432 | 数据库端口 |

**pgAdmin 默认登录：**
- 邮箱：`admin@openclaw.com`
- 密码：`admin`

### 5. 查看日志

```bash
# 查看所有服务日志
docker compose logs -f

# 查看 Bot 日志
docker compose logs -f bot

# 查看数据库日志
docker compose logs -f db
```

### 6. 停止服务

```bash
# 停止所有服务
docker compose down

# 停止并删除数据卷（谨慎使用）
docker compose down -v
```

---

## 测试 Bot

启动后，在 Telegram 中与你的 bot 交互：

```
/start - 欢迎消息
/help - 查看帮助
/status - 系统状态
/health - 健康检查
/jobs - 查看任务列表
```

---

## 数据库初始化

首次启动时，`init-db/init.sql` 会自动执行，创建以下表：

- `dim_security` - 证券维度表
- `dim_trade_calendar` - 交易日历
- `ods_daily_bar` - 日线行情
- `ods_position_snapshot` - 持仓快照
- `ods_trade` - 成交记录
- `dwd_factor_value` - 因子值
- `dm_strategy_signal` - 策略信号
- `dim_factor` - 因子元数据
- `dim_strategy` - 策略元数据

---

## 故障排查

**Bot 无法启动：**
- 检查 `TELEGRAM_BOT_TOKEN` 是否正确
- 检查 Docker 日志 `docker compose logs bot`

**数据库连接失败：**
- 等待数据库健康检查通过（约 10-15 秒）
- 检查 `DATABASE_URL` 配置

**容器持续重启：**
```bash
docker compose ps          # 查看容器状态
docker compose logs bot    # 查看 bot 日志
```

---

## 下一步

1. 配置 Tushare Token 后测试数据拉取
2. 配置 QMT 连接后测试持仓同步
3. 实现更多 Bot 命令和告警功能
