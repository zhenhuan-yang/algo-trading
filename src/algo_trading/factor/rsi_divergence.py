import numpy as np
import pandas as pd

from quant_trading.factor.base import IFactor


class RSIDivergence(IFactor):
    """RSI 背离检测因子

    计算 RSI、检测 Pivot Low/High、识别四种背离模式，并计算 ATR。

    基于 TradingView "RSI Long 5m SPY TQQQ" Pine Script 策略移植。

    输出列:
    - rsi: RSI 值
    - pivot_low: bool, pivot low 点
    - pivot_high: bool, pivot high 点
    - regular_bull_div: bool, 常规看涨背离 (价格 LL + RSI HL)
    - hidden_bull_div: bool, 隐藏看涨背离 (价格 HL + RSI LL)
    - regular_bear_div: bool, 常规看跌背离 (价格 HH + RSI LH)
    - hidden_bear_div: bool, 隐藏看跌背离 (价格 LH + RSI HH)
    - atr: Average True Range
    """

    def __init__(
        self,
        rsi_period: int = 17,
        pivot_left: int = 1,
        pivot_right: int = 2,
        range_lower: int = 5,
        range_upper: int = 60,
        atr_length: int = 15,
    ):
        self._rsi_period = rsi_period
        self._pivot_left = pivot_left
        self._pivot_right = pivot_right
        self._range_lower = range_lower
        self._range_upper = range_upper
        self._atr_length = atr_length

    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        # RSI (Wilder's smoothing, 与 TradingView 一致)
        df["rsi"] = self._compute_rsi(df["close"], self._rsi_period)

        # ATR
        df["atr"] = self._compute_atr(df, self._atr_length)

        # Pivot Low / High (基于 RSI)
        rsi = df["rsi"].values
        low = df["low"].values
        high = df["high"].values
        n = len(df)
        lbL = self._pivot_left
        lbR = self._pivot_right

        pivot_low = np.zeros(n, dtype=bool)
        pivot_high = np.zeros(n, dtype=bool)

        for i in range(lbL + lbR, n):
            center = i - lbR
            window = rsi[center - lbL: i + 1]
            if len(window) == lbL + lbR + 1 and not np.any(np.isnan(window)):
                # pivot low: rsi[center] 是区间最小值
                if rsi[center] == np.min(window):
                    pivot_low[i] = True
                # pivot high: rsi[center] 是区间最大值
                if rsi[center] == np.max(window):
                    pivot_high[i] = True

        df["pivot_low"] = pivot_low
        df["pivot_high"] = pivot_high

        # 背离检测
        reg_bull = np.zeros(n, dtype=bool)
        hid_bull = np.zeros(n, dtype=bool)
        reg_bear = np.zeros(n, dtype=bool)
        hid_bear = np.zeros(n, dtype=bool)

        # Bullish divergence: 在 pivot_low 点检测
        prev_pl_idx = -1  # 上一个 pivot low 的位置
        for i in range(n):
            if pivot_low[i]:
                center = i - lbR
                if prev_pl_idx >= 0:
                    prev_center = prev_pl_idx - lbR
                    bars_since = i - prev_pl_idx
                    if self._range_lower <= bars_since <= self._range_upper:
                        # Regular Bullish: 价格 Lower Low + RSI Higher Low
                        if low[center] < low[prev_center] and rsi[center] > rsi[prev_center]:
                            reg_bull[i] = True
                        # Hidden Bullish: 价格 Higher Low + RSI Lower Low
                        if low[center] > low[prev_center] and rsi[center] < rsi[prev_center]:
                            hid_bull[i] = True
                prev_pl_idx = i

        # Bearish divergence: 在 pivot_high 点检测
        prev_ph_idx = -1  # 上一个 pivot high 的位置
        for i in range(n):
            if pivot_high[i]:
                center = i - lbR
                if prev_ph_idx >= 0:
                    prev_center = prev_ph_idx - lbR
                    bars_since = i - prev_ph_idx
                    if self._range_lower <= bars_since <= self._range_upper:
                        # Regular Bearish: 价格 Higher High + RSI Lower High
                        if high[center] > high[prev_center] and rsi[center] < rsi[prev_center]:
                            reg_bear[i] = True
                        # Hidden Bearish: 价格 Lower High + RSI Higher High
                        if high[center] < high[prev_center] and rsi[center] > rsi[prev_center]:
                            hid_bear[i] = True
                prev_ph_idx = i

        df["regular_bull_div"] = reg_bull
        df["hidden_bull_div"] = hid_bull
        df["regular_bear_div"] = reg_bear
        df["hidden_bear_div"] = hid_bear

        return df

    @staticmethod
    def _compute_rsi(close: pd.Series, period: int) -> pd.Series:
        """Wilder's RSI (与 TradingView 内置 rsi() 一致)"""
        delta = close.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = (-delta).where(delta < 0, 0.0)

        # Wilder's smoothing: 第一个值用 SMA，之后用 EMA(alpha=1/period)
        avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    @staticmethod
    def _compute_atr(df: pd.DataFrame, length: int) -> pd.Series:
        """Average True Range"""
        high = df["high"]
        low = df["low"]
        prev_close = df["close"].shift(1)

        tr = pd.concat([
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ], axis=1).max(axis=1)

        return tr.ewm(span=length, min_periods=length, adjust=False).mean()