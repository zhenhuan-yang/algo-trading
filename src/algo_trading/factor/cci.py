import numpy as np
import pandas as pd

from algo_trading.factor.base import IFactor


class CCI(IFactor):
    """Commodity Channel Index (Donald Lambert, 1980)

    CCI = (TP - MA(TP, N)) / (0.015 * MeanDeviation(TP, N))

    TP (典型价格) = (high + low + close) / 3

    0.015 是 Lambert 常数，使约 70-80% 的 CCI 值落在 [-100, +100] 之间。
    """

    def __init__(self, period: int = 14):
        self._period = period

    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        tp = (df["high"] + df["low"] + df["close"]) / 3
        tp_ma = tp.rolling(self._period).mean()
        tp_avedev = tp.rolling(self._period).apply(
            lambda x: np.abs(x - x.mean()).mean(), raw=True
        )

        # Lambert 常数 0.015 是 CCI 标准定义的一部分
        denominator = 0.015 * tp_avedev
        df["cci"] = np.where(denominator != 0, (tp - tp_ma) / denominator, 0)

        return df
