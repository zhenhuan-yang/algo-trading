from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from algo_trading.common.enums import Side, OrderType, OrderStatus


@dataclass
class Order:
    symbol: str
    side: Side
    qty: float
    order_type: OrderType = OrderType.MARKET
    limit_price: Optional[float] = None


@dataclass
class Fill:
    symbol: str
    side: Side
    qty: float
    price: float
    timestamp: datetime


@dataclass
class Position:
    symbol: str
    qty: float
    avg_price: float
    market_value: float
