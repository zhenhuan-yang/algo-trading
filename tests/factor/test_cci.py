"""CCI.compute() 单元测试"""

import pandas as pd

from algo_trading.factor.cci import CCI

factor = CCI(period=14)


def test_output_column(ohlcv_uptrend):
    assert "cci" in factor.compute(ohlcv_uptrend).columns


def test_preserves_datetime_index(ohlcv_uptrend):
    assert isinstance(factor.compute(ohlcv_uptrend).index, pd.DatetimeIndex)


def test_no_mutation(ohlcv_uptrend):
    copy = ohlcv_uptrend.copy()
    factor.compute(ohlcv_uptrend)
    pd.testing.assert_frame_equal(ohlcv_uptrend, copy)


def test_positive_on_uptrend(ohlcv_all_up):
    assert factor.compute(ohlcv_all_up)["cci"].iloc[-1] > 0


def test_negative_on_downtrend(ohlcv_all_down):
    assert factor.compute(ohlcv_all_down)["cci"].iloc[-1] < 0
