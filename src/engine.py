import logging
from datetime import datetime, timedelta
from typing import List, Optional

import pandas as pd

from algo_trading.universe.base import IUniverse
from algo_trading.data.base import IBarDataHandler
from algo_trading.factor.base import IFactor
from algo_trading.strategy.base import IStrategy
from algo_trading.portfolio.base import IPortfolioManager
from algo_trading.broker.base import IBroker

logger = logging.getLogger(__name__)


class Engine:
    """Pipeline 编排器

    Universe → Data → Factor → Strategy → Portfolio → Broker
    """

    def __init__(
        self,
        universe: IUniverse,
        data_handler: IBarDataHandler,
        factors: List[IFactor],
        strategy: IStrategy,
        portfolio: IPortfolioManager,
        broker: IBroker,
        timeframe: str = "1d",
    ):
        self._universe = universe
        self._data = data_handler
        self._factors = factors
        self._strategy = strategy
        self._portfolio = portfolio
        self._broker = broker
        self._timeframe = timeframe

    def run(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        dry_run: bool = False,
    ):
        """执行完整 pipeline

        Args:
            start_time: 数据开始时间，默认 1 年前
            end_time: 数据结束时间，默认今天
            dry_run: True 则只生成信号不下单
        """
        end_time = end_time or datetime.now()
        start_time = start_time or end_time - timedelta(days=365)

        logger.info("start=%s end=%s dry_run=%s", start_time.date(), end_time.date(), dry_run)

        # 1. Universe
        symbols = self._universe.get_symbols()
        logger.info("[Universe] %d symbols: %s", len(symbols), symbols)

        # 2. Data
        logger.info("[Data] fetching bars ...")
        bars = self._data.get_bars(symbols, start_time, end_time, self._timeframe)
        empty_symbols = [s for s, df in bars.items() if df.empty]
        logger.info("[Data] fetched %d symbols, %d empty: %s", len(bars), len(empty_symbols), empty_symbols)

        # 3. Factor + Strategy (per symbol)
        buy_signals, sell_signals = [], []
        signals = {}
        for symbol, df in bars.items():
            if df.empty:
                continue

            for factor in self._factors:
                df = factor.compute(df)

            df = self._strategy.generate_signals(df)

            # 取最后一行的信号
            last = df.iloc[-1]
            if last.get("buy_signal", 0) == 1:
                signals[symbol] = 1
                buy_signals.append(symbol)
            elif last.get("sell_signal", 0) == 1:
                signals[symbol] = -1
                sell_signals.append(symbol)

        logger.info("[Strategy] buy=%s", buy_signals)
        logger.info("[Strategy] sell=%s", sell_signals)

        if not signals or dry_run:
            logger.info("[Engine] %s", "dry run, skipping orders" if dry_run else "no signals, done")
            return signals

        # 4. Portfolio
        positions = self._broker.get_positions()
        account = self._broker.get_account()
        logger.info("[Portfolio] cash=%.2f, portfolio_value=%.2f, positions=%s", account.cash, account.portfolio_value, list(positions.keys()))
        orders = self._portfolio.generate_orders(signals, positions, account)
        logger.info("[Portfolio] %d orders: %s", len(orders), [(o.side.value, o.symbol, o.notional or o.qty) for o in orders])

        # 5. Broker
        fills = self._broker.submit_orders(orders)
        for fill in fills:
            logger.info("[Broker] %s %s qty=%.4f price=%.4f", fill.side.value, fill.symbol, fill.qty, fill.price)

        logger.info("[Engine] done, %d fills", len(fills))
        return signals

