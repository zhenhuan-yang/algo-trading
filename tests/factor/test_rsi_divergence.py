"""RSIDivergence.compute() 单元测试"""

import pandas as pd

from algo_trading.factor.rsi_divergence import RSIDivergence

factor = RSIDivergence(rsi_period=17, atr_length=15)


class TestOutputSchema:

    def test_columns(self, ohlcv_uptrend):
        df = factor.compute(ohlcv_uptrend)
        expected = {"rsi", "atr", "pivot_low", "pivot_high",
                    "regular_bull_div", "hidden_bull_div",
                    "regular_bear_div", "hidden_bear_div"}
        assert expected.issubset(set(df.columns))

    def test_preserves_datetime_index(self, ohlcv_uptrend):
        df = factor.compute(ohlcv_uptrend)
        assert isinstance(df.index, pd.DatetimeIndex)
        assert str(df.index.tz) == "UTC"

    def test_no_mutation(self, ohlcv_uptrend):
        copy = ohlcv_uptrend.copy()
        factor.compute(ohlcv_uptrend)
        pd.testing.assert_frame_equal(ohlcv_uptrend, copy)


class TestRSI:

    def test_range(self, ohlcv_uptrend):
        rsi = factor.compute(ohlcv_uptrend)["rsi"].dropna()
        assert (rsi >= 0).all() and (rsi <= 100).all()

    def test_high_on_all_up(self, ohlcv_all_up):
        assert factor.compute(ohlcv_all_up)["rsi"].iloc[-1] > 90

    def test_low_on_all_down(self, ohlcv_all_down):
        assert factor.compute(ohlcv_all_down)["rsi"].iloc[-1] < 10


class TestATR:

    def test_positive(self, ohlcv_uptrend):
        assert (factor.compute(ohlcv_uptrend)["atr"].dropna() > 0).all()
