from abc import ABC, abstractmethod
from typing import List


class IUniverse(ABC):
    @abstractmethod
    def get_symbols(self) -> List[str]:
        """
        返回当前候选标的池中的所有股票代码。
        实现可以是静态列表、指数成分股、或基于条件的动态筛选。
        """
        pass
