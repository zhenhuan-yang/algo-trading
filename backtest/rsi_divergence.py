"""RSI Divergence 策略回测

用法: uv run python backtest/rsi_divergence.py --start 2025-01-01 --end 2025-12-31
产物: data/backtest/ 下的 report.html, trades.csv, stats_by_symbol.csv
"""

import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import quantstats as qs
import vectorbt as vbt

from algo_trading.data.alpaca import AlpacaBarDataHandler
from algo_trading.factor.rsi_divergence import RSIDivergence
from algo_trading.strategy.rsi_divergence import RSIDivergenceStrategy

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("data/backtest")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

parser = argparse.ArgumentParser(description="RSI Divergence 策略回测")
parser.add_argument("--start", type=str, default=(datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d"))
parser.add_argument("--end", type=str, default=datetime.now().strftime("%Y-%m-%d"))
args = parser.parse_args()

# ── 参数（和 scripts/run_rsi_divergence.py 保持一致）──
SYMBOLS = ["VOO", "TQQQ"]
TIMEFRAME = "5m"
START = datetime.fromisoformat(args.start)
END = datetime.fromisoformat(args.end)
INIT_CASH = 100_000  # 每个 symbol 各 $100k，与 TradingView 一致
FEES = 0.001
SLIPPAGE = 0.001

# ── Factor + Strategy pipeline（复用 algo_trading）──
factor = RSIDivergence(rsi_period=17, atr_length=15)
strategy = RSIDivergenceStrategy(sl_type="ATR", stop_loss_multiplier=5.0)
bars = AlpacaBarDataHandler().get_bars(SYMBOLS, START, END, TIMEFRAME)

# 每个 symbol 独立回测，各自 $100k（与 TradingView 独立图表一致）
all_stats = []
all_returns = []
for symbol, df in bars.items():
    if df.empty:
        logger.warning("%s 无数据，跳过", symbol)
        continue
    df = factor.compute(df)
    df = strategy.generate_signals(df)

    close_s = df["close"]
    open_s = df["open"]
    # 信号延迟 1 bar + 用 open 价成交，模拟 TradingView 的 next bar open 执行
    entries_s = (df["buy_signal"] == 1).shift(1).fillna(False).astype(bool)
    exits_s = (df["sell_signal"] == 1).shift(1).fillna(False).astype(bool)

    logger.info(
        "%s: %d bars, %d entries, %d exits",
        symbol, len(df), int(entries_s.sum()), int(exits_s.sum()),
    )

    pf = vbt.Portfolio.from_signals(
        close=close_s,
        open=open_s,
        entries=entries_s,
        exits=exits_s,
        init_cash=INIT_CASH,
        fees=FEES,
        slippage=SLIPPAGE,
        freq="5min",
    )

    # trade log
    trades_path = OUTPUT_DIR / f"trades_{symbol}.csv"
    pf.trades.records_readable.to_csv(trades_path, index=False)
    logger.info("[Output] %s trades → %s", symbol, trades_path)

    # per-symbol stats
    METRICS = [
        "start", "end", "period",
        "total_return", "benchmark_return",
        "max_gross_exposure", "max_dd",
        "sharpe_ratio", "calmar_ratio", "sortino_ratio",
        "total_trades", "win_rate",
    ]
    stats = pf.stats(metrics=METRICS, silence_warnings=True)
    stats.name = symbol
    all_stats.append(stats)

    # per-symbol returns
    rets = pf.returns()
    rets.name = symbol
    all_returns.append(rets)

# ── 汇总输出 ──
stats_path = OUTPUT_DIR / "stats_by_symbol.csv"
pd.DataFrame(all_stats).to_csv(stats_path)
logger.info("[Output] per-symbol stats → %s", stats_path)

# quantstats: 等权合成组合收益
report_path = OUTPUT_DIR / "report.html"
combined_returns = pd.DataFrame(all_returns).T.mean(axis=1).dropna()
qs.reports.html(combined_returns, output=str(report_path))
logger.info("[Output] report → %s", report_path)

logger.info("[Done] 所有回测产物已保存到 %s", OUTPUT_DIR)
