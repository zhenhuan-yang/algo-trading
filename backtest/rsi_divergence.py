"""RSI Divergence 策略回测

用法: uv run python backtest/rsi_divergence.py
产物: data/backtest/ 下的 report.html, trades.csv, stats_by_symbol.csv
"""

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

# ── 参数（和 scripts/run_rsi_divergence.py 保持一致）──
SYMBOLS = ["VOO", "TQQQ", "ORCL"]
TIMEFRAME = "5m"
START = datetime.now() - timedelta(days=90)
END = datetime.now()
INIT_CASH = 100_000
FEES = 0.001
SLIPPAGE = 0.001

# ── Factor + Strategy pipeline（复用 algo_trading）──
factor = RSIDivergence(rsi_period=17, atr_length=15)
strategy = RSIDivergenceStrategy(sl_type="ATR", stop_loss_multiplier=5.0)
bars = AlpacaBarDataHandler().get_bars(SYMBOLS, START, END, TIMEFRAME)

closes, entries, exits = {}, {}, {}
for symbol, df in bars.items():
    if df.empty:
        logger.warning("%s 无数据，跳过", symbol)
        continue
    df = factor.compute(df)
    df = strategy.generate_signals(df)
    closes[symbol] = df["close"]
    entries[symbol] = df["buy_signal"] == 1
    exits[symbol] = df["sell_signal"] == 1

close_df = pd.DataFrame(closes)
entries_df = pd.DataFrame(entries).fillna(False).astype(bool)
exits_df = pd.DataFrame(exits).fillna(False).astype(bool)

logger.info(
    "%d symbols, %d bars, %d entries, %d exits",
    len(closes), len(close_df), int(entries_df.sum().sum()), int(exits_df.sum().sum()),
)

# ── vectorbt 回测 ──
pf = vbt.Portfolio.from_signals(
    close=close_df,
    entries=entries_df,
    exits=exits_df,
    init_cash=INIT_CASH,
    fees=FEES,
    slippage=SLIPPAGE,
    freq="5min",
)

# ── vectorbt 输出: trade log + per-symbol stats ──
trades_path = OUTPUT_DIR / "trades.csv"
pf.trades.records_readable.to_csv(trades_path, index=False)
logger.info("[Output] trades → %s", trades_path)

stats_path = OUTPUT_DIR / "stats_by_symbol.csv"
METRICS = [
    "start", "end", "period",
    "total_return", "benchmark_return",
    "max_gross_exposure", "max_dd",
    "sharpe_ratio", "calmar_ratio", "sortino_ratio",
    "total_trades", "win_rate",
]
pf.stats(group_by=False, metrics=METRICS, silence_warnings=True).to_csv(stats_path)
logger.info("[Output] per-symbol stats → %s", stats_path)

# ── quantstats 输出: HTML 报告 ──
report_path = OUTPUT_DIR / "report.html"
returns = pf.returns()
qs.reports.html(returns, output=str(report_path))
logger.info("[Output] report → %s", report_path)

logger.info("[Done] 所有回测产物已保存到 %s", OUTPUT_DIR)
