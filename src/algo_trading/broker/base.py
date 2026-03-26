from abc import ABC, abstractmethod
from typing import List, Dict

from algo_trading.common.datatypes import Order, Fill, Position


class IBroker(ABC):
    """经纪商基类"""

    @abstractmethod
    def submit_orders(self, orders: List[Order]) -> List[Fill]:
        """提交订单并返回成交结果"""
        pass

    @abstractmethod
    def get_positions(self) -> Dict[str, Position]:
        """获取当前持仓"""
        pass

    @abstractmethod
    def get_account_value(self) -> float:
        """获取账户总价值"""
        pass
