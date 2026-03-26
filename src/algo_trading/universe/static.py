from typing import List

from algo_trading.universe.base import IUniverse


class StaticUniverse(IUniverse):
    """静态标的池"""

    def __init__(self, symbols: List[str]):
        self._symbols = symbols

    def get_symbols(self) -> List[str]:
        return self._symbols
