"""
Trading Bot Configuration
=========================
Halal Spot-Only Trading Bot for OKX
No leverage, no futures, no interest -- Sharia compliant.
"""

# ─── OKX API CREDENTIALS ───────────────────────────────────────────
# Loaded from environment variables (set in Render dashboard)
import os

OKX_API_KEY = os.environ.get("OKX_API_KEY", "")
OKX_SECRET_KEY = os.environ.get("OKX_SECRET_KEY", "")
OKX_PASSPHRASE = os.environ.get("OKX_PASSPHRASE", "")

# Set to True for paper trading (HIGHLY recommended to test first)
USE_DEMO = True

# ─── TRADING PAIRS ──────────────────────────────────────────────────
TRADING_PAIRS = [
    "OP/USDT",
    "HBAR/USDT",
    "ZETA/USDT",
]

# ─── PORTFOLIO SETTINGS ────────────────────────────────────────────
INITIAL_CAPITAL = 851.36  # Your current portfolio value
TARGET_CAPITAL = 10_000   # Your target

# Max % of capital to risk per single trade
MAX_RISK_PER_TRADE = 0.02  # 2%

# Max % of capital in a single token
MAX_ALLOCATION_PER_TOKEN = 0.40  # 40%

# Stop-loss percentage (per trade)
STOP_LOSS_PCT = 0.05  # 5%

# Take-profit percentage (per trade)
TAKE_PROFIT_PCT = 0.08  # 8%

# Trailing stop percentage (activates after hitting take-profit zone)
TRAILING_STOP_PCT = 0.03  # 3%

# ─── STRATEGY SETTINGS ─────────────────────────────────────────────

# Grid Trading (for sideways / ranging markets)
GRID_SETTINGS = {
    "enabled": True,
    "num_grids": 10,          # Number of grid levels
    "grid_range_pct": 0.15,   # 15% range above and below current price
    "order_size_pct": 0.05,   # 5% of capital per grid order
}

# DCA (Dollar Cost Averaging -- for accumulation in downtrends)
DCA_SETTINGS = {
    "enabled": True,
    "dip_threshold_pct": 0.03,   # Buy when price dips 3%
    "max_dca_orders": 5,         # Max DCA buys per token
    "dca_multiplier": 1.5,       # Each DCA order is 1.5x the previous
    "base_order_pct": 0.03,      # 3% of capital for first DCA order
}

# Momentum / Trend Following
MOMENTUM_SETTINGS = {
    "enabled": True,
    "ema_fast": 9,
    "ema_slow": 21,
    "ema_trend": 50,
    "rsi_period": 14,
    "rsi_oversold": 30,
    "rsi_overbought": 70,
    "macd_fast": 12,
    "macd_slow": 26,
    "macd_signal": 9,
    "volume_surge_multiplier": 1.5,  # Volume must be 1.5x average
}

# Bollinger Band Mean Reversion
BOLLINGER_SETTINGS = {
    "enabled": True,
    "period": 20,
    "std_dev": 2.0,
    "buy_at_lower_band": True,
    "sell_at_upper_band": True,
}

# ─── TIMEFRAMES ─────────────────────────────────────────────────────
PRIMARY_TIMEFRAME = "15m"      # Main analysis timeframe
SECONDARY_TIMEFRAME = "1h"     # Confirmation timeframe
TREND_TIMEFRAME = "4h"         # Overall trend direction

# ─── RISK MANAGEMENT ───────────────────────────────────────────────
# Daily loss limit -- bot stops trading if daily loss exceeds this
MAX_DAILY_LOSS_PCT = 0.05      # 5% of portfolio

# Max number of open positions at once
MAX_OPEN_POSITIONS = 3

# Minimum USDT to keep as reserve (never trade this amount)
MIN_USDT_RESERVE = 50.0

# Cooldown after a losing trade (seconds)
LOSS_COOLDOWN_SECONDS = 300    # 5 minutes

# ─── BOT SETTINGS ──────────────────────────────────────────────────
SCAN_INTERVAL_SECONDS = 30     # How often to check markets
LOG_FILE = "trading_bot.log"
TRADE_HISTORY_FILE = "trade_history.json"
