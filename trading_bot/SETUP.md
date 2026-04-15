# OKX Halal Spot Trading Bot - Setup Guide

## Sharia Compliant: SPOT ONLY | No Leverage | No Futures | No Interest

---

## Step 1: Install Dependencies

```bash
cd trading_bot
pip install -r requirements.txt
```

## Step 2: Get Your OKX API Keys

1. Open OKX app or website
2. Go to **Profile > API > Create API Key**
3. Set permissions: **Read + Trade** (do NOT enable Withdraw)
4. Set IP whitelist (recommended for security)
5. Save your: API Key, Secret Key, Passphrase

## Step 3: Configure the Bot

Edit `config.py` and fill in your API credentials:

```python
OKX_API_KEY = "your-api-key-here"
OKX_SECRET_KEY = "your-secret-key-here"
OKX_PASSPHRASE = "your-passphrase-here"
```

## Step 4: Test with Demo Mode First

```bash
# Run analysis only (no trades)
python bot.py --analyze

# Run in demo/paper trading mode (default)
python bot.py
```

## Step 5: Go Live (when ready)

```bash
# Live trading with real money
python bot.py --live
```

---

## How It Works

### 4 Strategies Combined:

| Strategy | What It Does | Best Market |
|----------|-------------|-------------|
| **Momentum** | Follows trends using EMA/RSI/MACD | Trending up/down |
| **Bollinger** | Buys at lower band, sells at upper | Ranging/sideways |
| **DCA** | Buys dips progressively | Downtrends |
| **Grid** | Places orders at intervals | Low volatility |

### Risk Protection:
- 2% max risk per trade
- 5% daily loss limit (bot pauses)
- 40% max allocation per token
- Stop-loss on every position
- Trailing stop to lock in profits
- $50 USDT always kept as reserve

### Your Pairs:
- OP/USDT (Optimism)
- HBAR/USDT (Hedera)
- ZETA/USDT (ZetaChain)

---

## Important Notes

- **ALWAYS test in demo mode first**
- The bot scans every 30 seconds by default
- All trades are logged in `trade_history.json`
- Full logs saved to `trading_bot.log`
- **This is NOT guaranteed profit** - crypto is volatile
- **This is NOT financial advice**
