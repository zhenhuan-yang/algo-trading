import logging
import os
from typing import List, Dict, Optional
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from algo_trading.broker.base import IBroker
from algo_trading.common.datatypes import Order, Fill, Position, Account
from algo_trading.common.enums import Side
from algo_trading.utils.email import send_email

logger = logging.getLogger(__name__)


class AlpacaBroker(IBroker):
    """Alpaca Paper Trading Broker"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        paper: bool = True,
    ):
        self._api_key = api_key or os.getenv("ALPACA_API_KEY")
        self._secret_key = secret_key or os.getenv("ALPACA_SECRET_KEY")
        if not self._api_key or not self._secret_key:
            raise ValueError(
                "需要提供 api_key/secret_key 或设置环境变量 "
                "ALPACA_API_KEY / ALPACA_SECRET_KEY"
            )
        self._client = TradingClient(self._api_key, self._secret_key, paper=paper)

    def submit_orders(self, orders: List[Order]) -> List[Fill]:
        fills = []
        for order in orders:
            # notional 和 qty 二选一，由 Order.__post_init__ 保证至少有一个
            sizing = {"notional": order.notional} if order.notional else {"qty": order.qty}
            req = MarketOrderRequest(
                symbol=order.symbol,
                side=order.side.value,
                time_in_force=order.time_in_force.value,
                **sizing,
            )

            result = self._client.submit_order(req)
            fills.append(Fill(
                order_id=str(result.id),
                symbol=result.symbol,
                side=order.side,
                qty=float(result.qty or result.notional or 0),
                price=float(result.filled_avg_price or 0),
                timestamp=result.filled_at or datetime.now(),
            ))

        if fills:
            lines = [
                f"  {f.side.value.upper()} {f.symbol}  "
                f"qty={f.qty}  price=${f.price:.2f}  "
                f"notional=${f.notional:.2f}"
                for f in fills
            ]
            send_email(
                subject=f"[Algo Trading] {len(fills)} fill(s) executed",
                body=f"成交时间: {datetime.now():%Y-%m-%d %H:%M:%S}\n\n" + "\n".join(lines),
            )

        return fills

    def get_positions(self) -> Dict[str, Position]:
        raw = self._client.get_all_positions()
        return {
            p.symbol: Position(
                symbol=p.symbol,
                qty=float(p.qty),
                avg_price=float(p.avg_entry_price),
                current_price=float(p.current_price),
            )
            for p in raw
        }

    def get_account(self) -> Account:
        raw = self._client.get_account()
        return Account(
            cash=float(raw.cash),
            buying_power=float(raw.buying_power),
            portfolio_value=float(raw.portfolio_value),
        )
