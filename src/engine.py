from datetime import datetime, timedelta
from typing import List, Optional

import pandas as pd

from algo_trading.universe.base import IUniverse
from algo_trading.data.base import IBarDataHandler
from algo_trading.factor.base import IFactor
from algo_trading.strategy.base import IStrategy
from algo_trading.portfolio.base import IPortfolioManager
from algo_trading.broker.base import IBroker


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
    ):
        self._universe = universe
        self._data = data_handler
        self._factors = factors
        self._strategy = strategy
        self._portfolio = portfolio
        self._broker = broker

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

        # 1. Universe
        symbols = self._universe.get_symbols()
        print(f"[Universe] {len(symbols)} symbols")

        # 2. Data
        bars = self._data.get_bars(symbols, start_time, end_time)
        print(f"[Data] fetched {len(bars)} symbols")

        # 3. Factor + Strategy (per symbol)
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
            elif last.get("sell_signal", 0) == 1:
                signals[symbol] = -1

        print(f"[Strategy] signals: {signals}")

        if not signals or dry_run:
            print(f"[Engine] {'dry run, skipping orders' if dry_run else 'no signals'}")
            return signals

        # 4. Portfolio
        positions = self._broker.get_positions()
        account_value = self._broker.get_account_value()
        orders = self._portfolio.generate_orders(signals, positions, account_value)
        print(f"[Portfolio] {len(orders)} orders")

        # 5. Broker
        fills = self._broker.submit_orders(orders)
        for fill in fills:
            print(f"[Broker] {fill.side.value} {fill.symbol} qty={fill.qty} price={fill.price}")

        return signals


if __name__ == "__main__":
    import os
    from algo_trading.universe.static import StaticUniverse
    from algo_trading.data.alpaca import AlpacaBarDataHandler
    from algo_trading.factor.cci import CCI
    from algo_trading.strategy.base import IStrategy
    from algo_trading.portfolio.simple import SimplePortfolioManager
    from algo_trading.broker.alpaca import AlpacaBroker

    # 中概股 (匹配 archive/strategies/polygon_ticker_fetcher.py)
    CHINESE_STOCKS = sorted(set([
        'BABA', 'JD', 'PDD', 'NIO', 'XPEV', 'LI', 'BILI', 'BIDU', 'NTES', 'TME',
        'EDU', 'TAL', 'HTHT', 'GDS', 'IQ', 'KC', 'ATHM', 'HUYA', 'VIPS', 'ZH',
        'DADA', 'BGNE', 'ZLAB', 'YUMC', 'MNSO', 'API', 'TIGR', 'FUTU', 'UP',
        'QFIN', 'LU', 'BEKE', 'TCOM', 'ZTO', 'BZUN', 'WB', 'MOMO', 'YY', 'SOHU',
        'NOAH', 'LX', 'FINV', 'GOTU', 'HOLI', 'NIU', 'TUYA', 'WBAI', 'JKS',
        'DQ', 'CSIQ', 'RENN', 'LEJU', 'EH', 'CANG', 'UXIN', 'KNDI', 'CAAS',
        'XNET', 'SOGO', 'WIMI', 'YRD', 'XYF', 'HUIZ', 'QTT', 'CCNC', 'CMCM',
        'LIZI', 'TOUR', 'CTK', 'NCTY', 'ZJYL', 'AMBO', 'REDU', 'COE', 'ONE',
        'DLNG', 'FENG', 'GLG', 'GRCL', 'JZ', 'TEDU', 'LKCO', 'AIHS', 'DTSS',
        'XIN', 'SINO', 'QH', 'SEED', 'WAFU', 'WEI', 'CNTF', 'JRJC', 'BEDU',
        'MOHO', 'RYB', 'SFUN', 'YIN', 'CNET', 'CCM', 'CLPS', 'DOGZ', 'HGSH',
        'HLG', 'HX', 'OGEN', 'QSG', 'RLYB', 'SG', 'TC', 'UTME', 'ZCMD',
        'PETZ', 'PHCF', 'RAAS', 'RCON', 'SDH', 'SNDA', 'SXTC', 'THTI', 'UCAR',
        'XRS', 'YI', 'YJ', 'ZKIN', 'LUNG',
    ]))

    engine = Engine(
        universe=StaticUniverse(CHINESE_STOCKS),
        data_handler=AlpacaBarDataHandler(),
        factors=[
            CCI(14),
        ],
        strategy=MultiPeriodResonance(),
        portfolio=SimplePortfolioManager(),
        broker=AlpacaBroker(),
    )
    # 5 年数据确保多周期指标有足够 warmup
    # DRY_RUN 环境变量控制是否实盘下单，默认 dry run
    dry_run = os.getenv("DRY_RUN", "true").lower() != "false"
    engine.run(
        start_time=datetime(2020, 1, 1),
        dry_run=dry_run,
    )
