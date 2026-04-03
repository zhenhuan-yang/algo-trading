"""SimplePortfolioManager.generate_orders() 单元测试"""

from algo_trading.common.datatypes import Account, Position
from algo_trading.common.enums import Side
from algo_trading.portfolio.simple import SimplePortfolioManager


ACCOUNT = Account(cash=100_000, buying_power=200_000, portfolio_value=100_000)


class TestGenerateOrders:

    def setup_method(self):
        self.pm = SimplePortfolioManager(max_positions=3)

    def test_buy_creates_order(self):
        orders = self.pm.generate_orders({"AAPL": 1}, {}, ACCOUNT)
        assert len(orders) == 1
        assert orders[0].side == Side.BUY

    def test_no_double_buy(self):
        positions = {"AAPL": Position("AAPL", 10, 150.0, 155.0)}
        orders = self.pm.generate_orders({"AAPL": 1}, positions, ACCOUNT)
        assert all(o.side != Side.BUY for o in orders)

    def test_max_positions_cap(self):
        positions = {
            "AAPL": Position("AAPL", 10, 150, 155),
            "GOOG": Position("GOOG", 5, 2800, 2850),
            "MSFT": Position("MSFT", 8, 400, 410),
        }
        orders = self.pm.generate_orders({"TSLA": 1}, positions, ACCOUNT)
        assert all(o.side != Side.BUY for o in orders)

    def test_sell_with_position(self):
        positions = {"AAPL": Position("AAPL", 10, 150.0, 155.0)}
        orders = self.pm.generate_orders({"AAPL": -1}, positions, ACCOUNT)
        assert len(orders) == 1
        assert orders[0].side == Side.SELL
        assert orders[0].qty == 10

    def test_sell_without_position(self):
        orders = self.pm.generate_orders({"AAPL": -1}, {}, ACCOUNT)
        assert len(orders) == 0

    def test_no_signals(self):
        orders = self.pm.generate_orders({}, {}, ACCOUNT)
        assert len(orders) == 0
