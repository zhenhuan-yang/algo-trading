from typing import List, Dict

from quant_trading.common.datatypes import Order, Position, Account
from quant_trading.common.enums import Side
from quant_trading.portfolio.base import IPortfolioManager


class SimplePortfolioManager(IPortfolioManager):
    """等权重投资组合管理

    max_positions: 最大持仓数，每个仓位分配 portfolio_value / max_positions。
                   None 表示不限，按当前买单数均分可用现金。
    """

    def __init__(self, max_positions: int | None = None):
        self._max_positions = max_positions

    def generate_orders(
        self,
        signals: Dict[str, int],
        positions: Dict[str, Position],
        account: Account,
    ) -> List[Order]:
        orders = []
        current_count = len(positions)

        buy_symbols = [
            s for s, sig in signals.items()
            if sig == 1 and s not in positions
            and (not self._max_positions or current_count < self._max_positions)
        ]

        if self._max_positions:
            # 等权目标金额，但不超过可用现金
            notional_per_buy = min(
                account.portfolio_value / self._max_positions,
                account.cash / len(buy_symbols) if buy_symbols else 0,
            )
        elif buy_symbols:
            notional_per_buy = account.cash / len(buy_symbols)
        else:
            notional_per_buy = 0

        for symbol in buy_symbols:
            orders.append(Order(
                symbol=symbol,
                side=Side.BUY,
                notional=notional_per_buy,
            ))
            current_count += 1

        for symbol, signal in signals.items():
            if signal == -1 and symbol in positions:
                orders.append(Order(
                    symbol=symbol,
                    side=Side.SELL,
                    qty=positions[symbol].qty,
                ))

        return orders