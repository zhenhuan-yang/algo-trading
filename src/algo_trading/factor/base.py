from abc import ABC, abstractmethod

import pandas as pd


class IFactor(ABC):
    """因子基类

    纯 transform：接收 DataFrame，返回添加了因子列的 DataFrame。
    """

    @abstractmethod
    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算因子

        Args:
            df: 输入数据，具体所需列由子类定义

        Returns:
            添加了因子列的 DataFrame
        """
        pass