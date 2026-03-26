from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List

import pandas as pd


class IDataHandler(ABC):
    """数据访问基础接口

    K线数据、另类数据等各自继承并定义具体方法。
    """
    pass


class IBarDataHandler(IDataHandler):
    """K线行情数据接口"""

    @abstractmethod
    def get_bars(
        self,
        symbols: List[str],
        start_time: datetime,
        end_time: datetime,
        timeframe: str = "1d",
    ) -> Dict[str, pd.DataFrame]:
        """获取历史 K 线数据

        Args:
            symbols: 标的代码列表
            start_time: 开始时间（含）
            end_time: 结束时间（含）
            timeframe: K线周期 ("1d", "1w", "1M")

        Returns:
            Dict[symbol, DataFrame]
        """
        ...
