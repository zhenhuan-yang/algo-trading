from typing import List, Dict

from algo_trading.common.datatypes import Order, Position
from algo_trading.common.enums import Side, OrderType
from algo_trading.portfolio.base import IPortfolioManager


class SimplePortfolioManager(IPortfolioManager):
    """简单全仓买卖

    买入信号 → 用全部可用资金买入
    卖出信号 → 卖出全部持仓
    """

    def generate_orders(
        self,
        signals: Dict[str, int],
        positions: Dict[str, Position],
        account_value: float,
    ) -> List[Order]:
        orders = []

        for symbol, signal in signals.items():
            if signal == 1 and symbol not in positions:
                # 全仓买入：用账户价值估算股数（实际价格由 broker 决定）
                orders.append(Order(
                    symbol=symbol,
                    side=Side.BUY,
                    qty=0,  # 0 表示全仓，由 broker 按市价计算
                    order_type=OrderType.MARKET,
                ))
            elif signal == -1 and symbol in positions:
                orders.append(Order(
                    symbol=symbol,
                    side=Side.SELL,
                    qty=positions[symbol].qty,
                    order_type=OrderType.MARKET,
                ))

        return orders
