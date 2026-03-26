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
| **Factor** | 因子计算 (纯 transform) |`CCI` |
| **Strategy** | 信号条件 (stateless, 不跟踪 position) | `IStrategy` |
| **Portfolio** | 订单生成 (position-aware) | `SimplePortfolioManager` |
| **Broker** | 订单执行 + 持仓查询 | `AlpacaBroker` (paper trading) |
| **Engine** | Pipeline 编排 (通用) | `Engine` |

### 设计原则

- **Factor = Feature engineering**: 纯数据变换
- **Strategy = Model**: 输出 raw conditions (买入/卖出条件是否满足)，不跟踪持仓状态
- **Portfolio = Position gate**: 结合 broker 真实持仓过滤信号，防止重复买卖
- **Engine**: 完全通用，不感知具体策略逻辑

## Setup

```sh
uv sync
```

创建 `.env`：
```
ALPACA_LIVE_API_KEY=your_key
ALPACA_LIVE_SECRET_KEY=your_secret
ALPACA_PAPER_API_KEY=your_key
ALPACA_PAPER_SECRET_KEY=your_secret
```

## Usage

```
uv run python -m algo_trading.engine
```

## Project Structure

```
src/algo_trading/
├── engine.py        # Pipeline 编排器 (通用)
├── common/          # enums, datatypes (Order, Fill, Position)
├── data/            # IBarDataHandler, AlpacaBarDataHandler
├── factor/          # IFactor, CCI
├── strategy/        # IStrategy
├── universe/        # IUniverse, StaticUniverse, AlpacaUniverse
├── portfolio/       # IPortfolioManager, SimplePortfolioManager
└── broker/          # IBroker, AlpacaBroker
```
