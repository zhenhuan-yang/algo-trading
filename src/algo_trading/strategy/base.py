from abc import ABC, abstractmethod

import pandas as pd


class IStrategy(ABC):
    """策略基类

    接收已计算 factor 的 DataFrame，生成交易信号。
    """

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """生成交易信号

        Args:
            df: 包含 factor 列的 DataFrame，具体所需列由子类定义

        Returns:
            添加了信号列的 DataFrame
        """
        pass