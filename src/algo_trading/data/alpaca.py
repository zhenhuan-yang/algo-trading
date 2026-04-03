import os
from datetime import datetime
from typing import Dict, List, Optional

from dotenv import load_dotenv
import pandas as pd

load_dotenv()
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

from algo_trading.data.base import IBarDataHandler

# 我们的 timeframe 字符串 -> Alpaca TimeFrame 映射
_TIMEFRAME_MAP = {
    "1m": TimeFrame(1, TimeFrameUnit.Minute),
    "5m": TimeFrame(5, TimeFrameUnit.Minute),
    "15m": TimeFrame(15, TimeFrameUnit.Minute),
    "30m": TimeFrame(30, TimeFrameUnit.Minute),
    "1h": TimeFrame(1, TimeFrameUnit.Hour),
    "1d": TimeFrame(1, TimeFrameUnit.Day),
    "1w": TimeFrame(1, TimeFrameUnit.Week),
    "1M": TimeFrame(1, TimeFrameUnit.Month),
}


class AlpacaBarDataHandler(IBarDataHandler):
    """Alpaca 历史 K 线数据实现"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        feed: str = "iex",
    ):
        """
        Args:
            api_key: Alpaca API Key，默认从环境变量 ALPACA_API_KEY 读取
            secret_key: Alpaca Secret Key，默认从环境变量 ALPACA_SECRET_KEY 读取
            feed: 数据源 ("iex" 免费, "sip" 付费全市场)
        """
        self._api_key = api_key or os.getenv("ALPACA_API_KEY")
        self._secret_key = secret_key or os.getenv("ALPACA_SECRET_KEY")
        if not self._api_key or not self._secret_key:
            raise ValueError(
                "需要提供 api_key/secret_key 或设置环境变量 "
                "ALPACA_API_KEY / ALPACA_SECRET_KEY"
            )
        self._feed = feed
        self._client = StockHistoricalDataClient(self._api_key, self._secret_key)

    def get_bars(
        self,
        symbols: List[str],
        start_time: datetime,
        end_time: datetime,
        timeframe: str = "1d",
    ) -> Dict[str, pd.DataFrame]:
        tf = _TIMEFRAME_MAP.get(timeframe)
        if tf is None:
            raise ValueError(
                f"不支持的 timeframe: {timeframe}，"
                f"可选: {list(_TIMEFRAME_MAP.keys())}"
            )

        request = StockBarsRequest(
            symbol_or_symbols=symbols,
            timeframe=tf,
            start=start_time,
            end=end_time,
            feed=self._feed,
        )
        bars = self._client.get_stock_bars(request)

        # bars.df 返回 MultiIndex (symbol, timestamp) 的 DataFrame
        raw_df = bars.df

        result: Dict[str, pd.DataFrame] = {}
        for symbol in symbols:
            if symbol in raw_df.index.get_level_values(0):
                df = raw_df.loc[symbol].copy()
                df = df.rename(columns={"trade_count": "trades"})
                # 统一 DatetimeIndex: UTC、命名、排序、去重
                df.index = df.index.tz_convert("UTC")
                df.index.name = "timestamp"
                df = df.sort_index()
                df = df[~df.index.duplicated(keep="last")]
                result[symbol] = df
            else:
                result[symbol] = pd.DataFrame(
                    columns=["open", "high", "low", "close", "volume", "vwap", "trades"],
                    index=pd.DatetimeIndex([], name="timestamp", tz="UTC"),
                )

        return result
