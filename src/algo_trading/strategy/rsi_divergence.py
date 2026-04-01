import pandas as pd

from algo_trading.strategy.base import IStrategy


class RSIDivergenceStrategy(IStrategy):
    """RSI 背离策略

    基于 TradingView "RSI Long 5m SPY TQQQ" Pine Script 策略移植。

    买入条件:
    - Regular Bullish Divergence 或 Hidden Bullish Divergence

    卖出条件 (按 sl_type 分模式):
    - NONE: RSI 上穿 take_profit_rsi 或 Regular Bearish Divergence
    - PERC: 价格跌破 trailing stop (low - close * stop_loss_pct)
    - ATR:  价格跌破 trailing stop (low - stop_loss_multiplier * ATR)

    Trailing stop 只在持仓时更新，只升不降。

    注意: position 管理由 PortfolioManager 负责，策略只输出信号。
    """

    def __init__(
        self,
        sl_type: str = "ATR",
        take_profit_rsi: float = 80,
        stop_loss_pct: float = 0.05,
        stop_loss_multiplier: float = 5.0,
        use_hidden_bull: bool = True,
        use_hidden_bear: bool = False,
    ):
        if sl_type not in ("ATR", "PERC", "NONE"):
            raise ValueError(f"sl_type 必须是 ATR/PERC/NONE，收到: {sl_type}")
        self._sl_type = sl_type
        self._take_profit_rsi = take_profit_rsi
        self._stop_loss_pct = stop_loss_pct
        self._stop_loss_multiplier = stop_loss_multiplier
        self._use_hidden_bull = use_hidden_bull
        self._use_hidden_bear = use_hidden_bear

    def _compute_sl_val(self, close: float, atr: float) -> float:
        """计算止损偏移量"""
        if self._sl_type == "ATR":
            return self._stop_loss_multiplier * atr
        elif self._sl_type == "PERC":
            return close * self._stop_loss_pct
        return 0.0

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """生成交易信号

        期望的 factor 列: rsi, atr, pivot_low, pivot_high,
        regular_bull_div, hidden_bull_div, regular_bear_div, hidden_bear_div
        """
        df = df.copy()
        n = len(df)

        rsi = df["rsi"].values
        low = df["low"].values
        close = df["close"].values
        atr = df["atr"].values
        reg_bull = df["regular_bull_div"].values
        hid_bull = df["hidden_bull_div"].values
        reg_bear = df["regular_bear_div"].values
        hid_bear = df["hidden_bear_div"].values

        buy_signal = [0] * n
        sell_signal = [0] * n

        # 模拟持仓状态，用于 trailing stop 和避免重复信号
        in_position = False
        trailing_sl = 0.0

        for i in range(1, n):
            # 买入条件
            bull_cond = reg_bull[i] or (self._use_hidden_bull and hid_bull[i])
            if bull_cond and not in_position:
                buy_signal[i] = 1
                in_position = True
                trailing_sl = low[i] - self._compute_sl_val(close[i], atr[i])
                continue

            if not in_position:
                continue

            if self._sl_type == "NONE":
                # NONE 模式: RSI 止盈 或 Bearish Divergence
                rsi_crossover = rsi[i] > self._take_profit_rsi and rsi[i - 1] <= self._take_profit_rsi
                bear_cond = reg_bear[i] or (self._use_hidden_bear and hid_bear[i])
                if rsi_crossover or bear_cond:
                    sell_signal[i] = 1
                    in_position = False
            else:
                # ATR/PERC 模式: 只看 trailing stop
                new_sl = low[i] - self._compute_sl_val(close[i], atr[i])
                trailing_sl = max(trailing_sl, new_sl)
                if close[i] < trailing_sl:
                    sell_signal[i] = 1
                    in_position = False
                    trailing_sl = 0.0

        df["buy_signal"] = buy_signal
        df["sell_signal"] = sell_signal

        return df