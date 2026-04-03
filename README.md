# algo-trading

轻量级量化交易平台 — Python native，模块化 pipeline 架构。

## Architecture

```
Universe → Data → Factor → Strategy → Portfolio → Broker
```

| 层 | 职责 | 实现 |
|---|------|------|
| **Universe** | 标的池 | `StaticUniverse`, `AlpacaUniverse` |
| **Data** | K线数据 | `AlpacaBarDataHandler` |
| **Factor** | 因子计算 (纯 transform) | `RSIDivergence`, `CCI` |
| **Strategy** | 信号条件 (stateless，不跟踪 position) | `RSIDivergenceStrategy` |
| **Portfolio** | 订单生成 (position-aware) | `SimplePortfolioManager` |
| **Broker** | 订单执行 + 持仓查询 | `AlpacaBroker` (paper trading) |
| **Engine** | Pipeline 编排 (通用) | `Engine` |

### 设计原则

- **Factor = Feature engineering**: 纯数据变换
- **Strategy = Model**: 输出 raw conditions，不跟踪持仓状态
- **Portfolio = Position gate**: 结合 broker 真实持仓过滤信号，防止重复买卖
- **Engine**: 完全通用，不感知具体策略逻辑

## Setup

```sh
uv sync
```

创建 `.env`：
```
ALPACA_API_KEY=your_key
ALPACA_SECRET_KEY=your_secret
```

## Run Locally

```sh
uv run python scripts/run_rsi_divergence.py
```

dry run 默认开启（不实际下单），实盘：

```sh
DRY_RUN=false uv run python scripts/run_rsi_divergence.py
```

## Deploy (AWS ECS + EventBridge)

### 云端架构

```
                          ┌───────────┐
                          │ ECR Image │
                          └─────┬─────┘
                                │ pull
┌─────────────┐  trigger  ┌─────▼─────┐  logs  ┌─────────────────┐
│ EventBridge │──────────→│ ECS Task  │───────→│ CloudWatch Logs │
│  (cron 5m)  │           │ (Fargate) │        │                 │
└─────────────┘           └───────────┘        └─────────────────┘
```

### 推送镜像

```sh
./deploy.sh
```

依赖 `~/.aws/credentials` 中的 `[algo-trading]` profile。

### AWS 控制台手动配置（一次性）

1. **ECR** — 创建仓库 `algo-trading`
2. **ECS** — 创建集群 `algo-trading`，任务定义 `rsi-divergence` 选 Fargate，image 填 ECR URL，设置环境变量：
   ```
   ALPACA_API_KEY     = <your_key>
   ALPACA_SECRET_KEY  = <your_secret>
   DRY_RUN            = false
   SMTP_USER          = <your_gmail>
   SMTP_PASSWORD      = <gmail_app_password>
   EMAIL_TO           = <recipient_email>
   ```
3. **IAM** — `ecsTaskExecutionRole` 需要：
   - Trust policy 信任 `ecs-tasks.amazonaws.com` 和 `events.amazonaws.com`
   - 附加 `AmazonECSTaskExecutionRolePolicy`（拉镜像 + 写日志）
   - Inline policy 包含 `ecs:RunTask` 和 `iam:PassRole`（供 EventBridge 调用）
4. **EventBridge** — 创建规则，schedule `cron(0/5 13-20 ? * MON-FRI *)`（美股交易时段，UTC），target 选 ECS cluster + 任务定义，role 选 `ecsTaskExecutionRole`
5. **CloudWatch** — 日志自动写入 `/ecs/rsi-divergence`

## Project Structure

```
├── Dockerfile             # 容器镜像（python:3.11-slim + uv）
├── deploy.sh              # 构建 & 推送 ECR 镜像
├── pyproject.toml         # 项目依赖
├── scripts/
│   └── run_rsi_divergence.py  # 策略入口
└── src/
    └── algo_trading/
        ├── engine.py          # Pipeline 编排器
        ├── common/            # enums, datatypes (Order, Fill, Position)
        ├── data/              # IBarDataHandler, AlpacaBarDataHandler
        ├── factor/            # IFactor, RSIDivergence, CCI
        ├── strategy/          # IStrategy, RSIDivergenceStrategy
        ├── universe/          # IUniverse, StaticUniverse, AlpacaUniverse
        ├── portfolio/         # IPortfolioManager, SimplePortfolioManager
        ├── broker/            # IBroker, AlpacaBroker
        └── utils/             # email 通知等工具函数
```
