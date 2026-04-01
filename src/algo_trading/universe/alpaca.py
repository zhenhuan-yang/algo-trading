import os
from typing import List, Optional

from dotenv import load_dotenv

load_dotenv()

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetAssetsRequest
from alpaca.trading.enums import AssetStatus, AssetClass

from algo_trading.universe.base import IUniverse


class AlpacaUniverse(IUniverse):
    """从 Alpaca 获取可交易美股标的池"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        paper: bool = True,
    ):
        self._api_key = api_key or os.getenv("ALPACA_API_KEY")
        self._secret_key = secret_key or os.getenv("ALPACA_SECRET_KEY")
        if not self._api_key or not self._secret_key:
            raise ValueError(
                "需要提供 api_key/secret_key 或设置环境变量 "
                "ALPACA_API_KEY / ALPACA_SECRET_KEY"
            )
        self._client = TradingClient(self._api_key, self._secret_key, paper=paper)

    def get_symbols(self) -> List[str]:
        request = GetAssetsRequest(
            status=AssetStatus.ACTIVE,
            asset_class=AssetClass.US_EQUITY,
        )
        assets = self._client.get_all_assets(request)
        return sorted([
            a.symbol for a in assets
            if a.tradable and a.shortable is not False
        ])
