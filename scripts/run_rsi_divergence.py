"""RSI Divergence 策略运行脚本

VOO + TQQQ, 5 分钟周期, 半仓等权
"""

import logging
import os
from datetime import datetime, timedelta

from quant_trading.universe.static import StaticUniverse
from quant_trading.data.alpaca import AlpacaBarDataHandler
from quant_trading.factor.rsi_divergence import RSIDivergence
from quant_trading.strategy.rsi_divergence import RSIDivergenceStrategy
from quant_trading.portfolio.simple import SimplePortfolioManager
from quant_trading.broker.alpaca import AlpacaBroker
from quant_trading.engine import Engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)

SYMBOLS = ["VOO", "TQQQ"]

engine = Engine(
    universe=StaticUniverse(SYMBOLS),
    data_handler=AlpacaBarDataHandler(),
    factors=[RSIDivergence(rsi_period=17, atr_length=15)],
    strategy=RSIDivergenceStrategy(
        sl_type="ATR",
        stop_loss_multiplier=5.0,
    ),
    portfolio=SimplePortfolioManager(max_positions=len(SYMBOLS)),
    broker=AlpacaBroker(),
    timeframe="5m",
)

# 5 分钟数据拉 30 天足够 RSI warmup
dry_run = os.getenv("DRY_RUN", "true").lower() != "false"
engine.run(
    start_time=datetime.now() - timedelta(days=30),
    dry_run=dry_run,
)