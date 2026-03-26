import os
from typing import List, Dict, Optional
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

from algo_trading.broker.base import IBroker
from algo_trading.common.datatypes import Order, Fill, Position
from algo_trading.common.enums import Side


class AlpacaBroker(IBroker):
    """Alpaca Paper Trading Broker"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        paper: bool = True,
    ):
        self._api_key = api_key or os.getenv("ALPACA_PAPER_API_KEY")
        self._secret_key = secret_key or os.getenv("ALPACA_PAPER_SECRET_KEY")
        if not self._api_key or not self._secret_key:
            raise ValueError(
                "需要提供 api_key/secret_key 或设置环境变量 "
                "ALPACA_PAPER_API_KEY / ALPACA_PAPER_SECRET_KEY"
            )
        self._client = TradingClient(self._api_key, self._secret_key, paper=paper)

    def submit_orders(self, orders: List[Order]) -> List[Fill]:
        fills = []
        for order in orders:
            side = OrderSide.BUY if order.side == Side.BUY else OrderSide.SELL

            if order.qty == 0 and order.side == Side.BUY:
                # 全仓买入：用 notional (金额) 下单
                account = self._client.get_account()
                cash = float(account.cash)
                req = MarketOrderRequest(
                    symbol=order.symbol,
                    notional=cash,
                    side=side,
                    time_in_force=TimeInForce.DAY,
                )
            else:
                req = MarketOrderRequest(
                    symbol=order.symbol,
                    qty=order.qty,
                    side=side,
                    time_in_force=TimeInForce.DAY,
                )

            result = self._client.submit_order(req)
            fills.append(Fill(
                symbol=result.symbol,
                side=order.side,
                qty=float(result.qty or result.notional or 0),
                price=float(result.filled_avg_price or 0),
                timestamp=result.filled_at or datetime.now(),
            ))

        return fills

    def get_positions(self) -> Dict[str, Position]:
        raw = self._client.get_all_positions()
        return {
            p.symbol: Position(
                symbol=p.symbol,
                qty=float(p.qty),
                avg_price=float(p.avg_entry_price),
                market_value=float(p.market_value),
            )
            for p in raw
        }

    def get_account_value(self) -> float:
        account = self._client.get_account()
        return float(account.portfolio_value)
