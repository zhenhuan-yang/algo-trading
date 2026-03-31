from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from quant_trading.common.enums import Side, OrderType, OrderStatus, TimeInForce


@dataclass
class Order:
    symbol: str
    side: Side
    order_type: OrderType = OrderType.MARKET
    time_in_force: TimeInForce = TimeInForce.GTC
    qty: Optional[float] = None
    notional: Optional[float] = None
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    trail_percent: Optional[float] = None
    order_id: Optional[str] = None

    def __post_init__(self):
        if self.qty and self.notional:
            raise ValueError("qty 和 notional 只能指定一个")
        if not self.qty and not self.notional:
            raise ValueError("qty 或 notional 必须指定一个")


@dataclass
class Fill:
    order_id: str
    symbol: str
    side: Side
    qty: float
    price: float
    timestamp: datetime

    @property
    def notional(self) -> float:
        return self.qty * self.price


@dataclass
class Position:
    symbol: str
    qty: float
    avg_price: float
    current_price: float

    @property
    def cost_basis(self) -> float:
        return self.qty * self.avg_price

    @property
    def market_value(self) -> float:
        return self.qty * self.current_price

    @property
    def unrealized_pnl(self) -> float:
        return self.market_value - self.cost_basis

    @property
    def unrealized_pnl_pct(self) -> float:
        return self.unrealized_pnl / self.cost_basis if self.cost_basis else 0.0


@dataclass
class Account:
    cash: float
    buying_power: float
    portfolio_value: float