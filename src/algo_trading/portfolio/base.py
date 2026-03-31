from abc import ABC, abstractmethod
from typing import List, Dict

from quant_trading.common.datatypes import Order, Position, Account


class IPortfolioManager(ABC):
    """投资组合管理基类

    将策略信号转化为具体订单。
    """

    @abstractmethod
    def generate_orders(
        self,
        signals: Dict[str, int],
        positions: Dict[str, Position],
        account: Account,
    ) -> List[Order]:
        """根据信号生成订单

        Args:
            signals: {symbol: signal} 1=买入, -1=卖出, 0=无操作
            positions: 当前持仓
            account: 账户信息

        Returns:
            订单列表
        """
        pass