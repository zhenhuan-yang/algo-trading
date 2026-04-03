"""共享 fixtures"""

import numpy as np
import pandas as pd
import pytest


def _build_ohlcv(close, spread=0.5):
    n = len(close)
    close = np.array(close, dtype=float)
    rng = np.random.default_rng(42)
    high = close + rng.uniform(0, spread, n)
    low = close - rng.uniform(0, spread, n)
    open_ = np.roll(close, 1)
    open_[0] = close[0]
    index = pd.date_range("2026-01-02 14:30", periods=n, freq="5min", tz="UTC", name="timestamp")
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close,
         "volume": rng.integers(1000, 10000, n).astype(float),
         "vwap": close, "trades": rng.integers(10, 200, n)},
        index=index,
    )


@pytest.fixture()
def ohlcv_uptrend():
    """50 根 K 线，稳步上涨"""
    return _build_ohlcv(np.linspace(100, 120, 50))


@pytest.fixture()
def ohlcv_downtrend():
    """50 根 K 线，稳步下跌"""
    return _build_ohlcv(np.linspace(120, 100, 50))


@pytest.fixture()
def ohlcv_all_up():
    """40 根 K 线，每根都涨"""
    return _build_ohlcv(list(range(100, 140)))


@pytest.fixture()
def ohlcv_all_down():
    """40 根 K 线，每根都跌"""
    return _build_ohlcv(list(range(140, 100, -1)))
