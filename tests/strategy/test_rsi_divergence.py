"""RSIDivergenceStrategy.generate_signals() 单元测试

输入: 模拟的 factor 输出 DataFrame (不依赖 RSIDivergence)
"""

import numpy as np
import pandas as pd
import pytest

from algo_trading.strategy.rsi_divergence import RSIDivergenceStrategy


def _make_factor_df(ohlcv):
    """给 OHLCV 加上全零 factor 列，模拟无信号场景"""
    df = ohlcv.copy()
    df["rsi"] = 50.0
    df["atr"] = 1.0
    for col in ("pivot_low", "pivot_high", "regular_bull_div",
                "hidden_bull_div", "regular_bear_div", "hidden_bear_div"):
        df[col] = False
    return df


class TestGenerateSignals:

    def setup_method(self):
        self.strategy = RSIDivergenceStrategy(sl_type="ATR", stop_loss_multiplier=5.0)

    def test_output_columns(self, ohlcv_uptrend):
        df = self.strategy.generate_signals(_make_factor_df(ohlcv_uptrend))
        assert "buy_signal" in df.columns and "sell_signal" in df.columns

    def test_signals_are_binary(self, ohlcv_uptrend):
        df = self.strategy.generate_signals(_make_factor_df(ohlcv_uptrend))
        assert set(df["buy_signal"].unique()).issubset({0, 1})
        assert set(df["sell_signal"].unique()).issubset({0, 1})

    def test_no_signal_without_divergence(self, ohlcv_uptrend):
        df = self.strategy.generate_signals(_make_factor_df(ohlcv_uptrend))
        assert df["buy_signal"].sum() == 0 and df["sell_signal"].sum() == 0

    def test_buy_on_regular_bull_div(self, ohlcv_uptrend):
        df = _make_factor_df(ohlcv_uptrend)
        df.iloc[10, df.columns.get_loc("regular_bull_div")] = True
        assert self.strategy.generate_signals(df)["buy_signal"].sum() >= 1

    def test_no_mutation(self, ohlcv_uptrend):
        original = _make_factor_df(ohlcv_uptrend)
        copy = original.copy()
        self.strategy.generate_signals(original)
        pd.testing.assert_frame_equal(original, copy)

    def test_preserves_datetime_index(self, ohlcv_uptrend):
        df = self.strategy.generate_signals(_make_factor_df(ohlcv_uptrend))
        assert isinstance(df.index, pd.DatetimeIndex)

    def test_invalid_sl_type(self):
        with pytest.raises(ValueError):
            RSIDivergenceStrategy(sl_type="INVALID")
