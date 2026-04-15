#!/usr/bin/env python3
"""
OKX Halal Spot Trading Bot — Web Dashboard
============================================
Sharia Compliant: SPOT ONLY | No Leverage | No Futures | No Interest
"""

import json
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import ccxt
import pandas as pd
from flask import Flask, jsonify, render_template, request

from trading_bot.config import (
    BOLLINGER_SETTINGS,
    DCA_SETTINGS,
    GRID_SETTINGS,
    INITIAL_CAPITAL,
    LOSS_COOLDOWN_SECONDS,
    MAX_ALLOCATION_PER_TOKEN,
    MAX_DAILY_LOSS_PCT,
    MAX_OPEN_POSITIONS,
    MAX_RISK_PER_TRADE,
    MIN_USDT_RESERVE,
    MOMENTUM_SETTINGS,
    OKX_API_KEY,
    OKX_PASSPHRASE,
    OKX_SECRET_KEY,
    PRIMARY_TIMEFRAME,
    SCAN_INTERVAL_SECONDS,
    SECONDARY_TIMEFRAME,
    STOP_LOSS_PCT,
    TAKE_PROFIT_PCT,
    TARGET_CAPITAL,
    TRADE_HISTORY_FILE,
    TRADING_PAIRS,
    TRAILING_STOP_PCT,
    TREND_TIMEFRAME,
    USE_DEMO,
)
from trading_bot.indicators import compute_all_indicators, support_resistance
from trading_bot.risk_manager import RiskManager
from trading_bot.strategies import Signal, StrategyEngine

app = Flask(__name__)

# ─── Bot State ──────────────────────────────────────────────────────
bot_state = {
    "running": False,
    "mode": "demo",
    "portfolio_value": INITIAL_CAPITAL,
    "target": TARGET_CAPITAL,
    "daily_pnl": 0.0,
    "total_pnl": 0.0,
    "trades_today": 0,
    "total_trades": 0,
    "win_rate": 0.0,
    "positions": {},
    "last_signals": {},
    "trade_history": [],
    "log_messages": [],
    "started_at": None,
    "last_scan": None,
}

exchange = None
strategy_engine = None
risk_manager = None
bot_thread = None


def log(msg: str, level: str = "info"):
    """Add a log message to the bot state."""
    entry = {
        "time": datetime.now(timezone.utc).strftime("%H:%M:%S"),
        "level": level,
        "message": msg,
    }
    bot_state["log_messages"].insert(0, entry)
    # Keep last 100 messages
    if len(bot_state["log_messages"]) > 100:
        bot_state["log_messages"] = bot_state["log_messages"][:100]


def init_exchange(demo: bool = True):
    """Initialize the OKX exchange connection."""
    global exchange
    config = {
        "apiKey": OKX_API_KEY,
        "secret": OKX_SECRET_KEY,
        "password": OKX_PASSPHRASE,
        "enableRateLimit": True,
        "options": {"defaultType": "spot"},
    }
    if demo:
        config["sandbox"] = True

    exchange = ccxt.okx(config)
    try:
        exchange.load_markets()
        log(f"Connected to OKX ({'Demo' if demo else 'Live'})")
        return True
    except Exception as e:
        log(f"Connection failed: {e}", "error")
        return False


def init_strategies():
    """Initialize strategy engine and risk manager."""
    global strategy_engine, risk_manager

    strategy_engine = StrategyEngine({
        "momentum": {**MOMENTUM_SETTINGS, "enabled": True},
        "bollinger": {**BOLLINGER_SETTINGS, "enabled": True},
        "dca": {**DCA_SETTINGS, "enabled": True},
        "grid": {**GRID_SETTINGS, "enabled": True},
    })

    risk_manager = RiskManager({
        "max_risk_per_trade": MAX_RISK_PER_TRADE,
        "max_allocation_per_token": MAX_ALLOCATION_PER_TOKEN,
        "stop_loss_pct": STOP_LOSS_PCT,
        "take_profit_pct": TAKE_PROFIT_PCT,
        "trailing_stop_pct": TRAILING_STOP_PCT,
        "max_daily_loss_pct": MAX_DAILY_LOSS_PCT,
        "max_open_positions": MAX_OPEN_POSITIONS,
        "min_usdt_reserve": MIN_USDT_RESERVE,
        "loss_cooldown_seconds": LOSS_COOLDOWN_SECONDS,
    })
    risk_manager.reset_daily(INITIAL_CAPITAL)


def fetch_ohlcv(symbol: str, timeframe: str = "15m", limit: int = 100) -> pd.DataFrame:
    """Fetch candle data from OKX."""
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)
        return df
    except Exception as e:
        log(f"Error fetching {symbol} data: {e}", "error")
        return pd.DataFrame()


def analyze_pair(symbol: str) -> dict:
    """Run full analysis on a trading pair."""
    df = fetch_ohlcv(symbol, PRIMARY_TIMEFRAME, 100)
    if df.empty:
        return {"action": "HOLD", "confidence": 0, "reasons": ["No data available"],
                "price": 0, "rsi": 0, "support": 0, "resistance": 0}

    analysis = strategy_engine.analyze(df, symbol)

    # Multi-timeframe confirmation
    df_h = fetch_ohlcv(symbol, SECONDARY_TIMEFRAME, 100)
    if not df_h.empty:
        secondary = strategy_engine.analyze(df_h, symbol)
        if secondary["action"] == analysis["action"]:
            analysis["confidence"] = min(analysis["confidence"] * 1.2, 1.0)
            analysis["reasons"].append(f"[MTF] 1h confirms {analysis['action']}")

    # Price history for chart (last 50 candles)
    analysis["chart_data"] = {
        "labels": [t.strftime("%H:%M") for t in df.index[-50:]],
        "prices": df["close"].tail(50).tolist(),
        "volumes": df["volume"].tail(50).tolist(),
        "bb_upper": df["bb_upper"].tail(50).tolist() if "bb_upper" in df.columns else [],
        "bb_lower": df["bb_lower"].tail(50).tolist() if "bb_lower" in df.columns else [],
        "ema_fast": df["ema_fast"].tail(50).tolist() if "ema_fast" in df.columns else [],
        "ema_slow": df["ema_slow"].tail(50).tolist() if "ema_slow" in df.columns else [],
    }

    return analysis


def execute_buy(symbol: str, usdt_amount: float, price: float):
    """Execute spot buy."""
    token = symbol.split("/")[0]
    quantity = usdt_amount / price

    log(f"BUY {quantity:.2f} {token} @ ${price:.6f} = ${usdt_amount:.2f}")

    trade = {
        "time": datetime.now(timezone.utc).isoformat(),
        "symbol": symbol,
        "action": "BUY",
        "price": price,
        "quantity": quantity,
        "value": usdt_amount,
    }
    bot_state["trade_history"].insert(0, trade)
    bot_state["total_trades"] += 1
    bot_state["trades_today"] += 1
    risk_manager.record_trade(symbol, "BUY", price, quantity)

    bot_state["positions"][symbol] = {
        "token": token,
        "entry_price": price,
        "quantity": quantity,
        "value": usdt_amount,
        "current_price": price,
        "pnl": 0,
        "pnl_pct": 0,
    }


def execute_sell(symbol: str, price: float):
    """Execute spot sell."""
    if symbol not in bot_state["positions"]:
        return

    pos = bot_state["positions"][symbol]
    token = pos["token"]
    entry = pos["entry_price"]
    qty = pos["quantity"]
    pnl = (price - entry) * qty
    pnl_pct = ((price - entry) / entry) * 100

    log(f"SELL {qty:.2f} {token} @ ${price:.6f} | PnL: ${pnl:+.2f} ({pnl_pct:+.1f}%)",
        "success" if pnl > 0 else "error")

    trade = {
        "time": datetime.now(timezone.utc).isoformat(),
        "symbol": symbol,
        "action": "SELL",
        "price": price,
        "quantity": qty,
        "value": price * qty,
        "pnl": round(pnl, 2),
        "pnl_pct": round(pnl_pct, 2),
    }
    bot_state["trade_history"].insert(0, trade)
    bot_state["total_trades"] += 1
    bot_state["trades_today"] += 1
    bot_state["daily_pnl"] += pnl
    bot_state["total_pnl"] += pnl

    risk_manager.record_trade(symbol, "SELL", price, qty, pnl)
    del bot_state["positions"][symbol]

    # Update win rate
    sells = [t for t in bot_state["trade_history"] if t["action"] == "SELL"]
    if sells:
        wins = sum(1 for t in sells if t.get("pnl", 0) > 0)
        bot_state["win_rate"] = (wins / len(sells)) * 100


def bot_cycle():
    """Single trading cycle."""
    portfolio_value = bot_state["portfolio_value"]
    usdt_available = portfolio_value - sum(
        p["value"] for p in bot_state["positions"].values()
    )

    for symbol in TRADING_PAIRS:
        try:
            analysis = analyze_pair(symbol)
            bot_state["last_signals"][symbol] = {
                "action": analysis["action"],
                "confidence": analysis["confidence"],
                "price": analysis["price"],
                "rsi": analysis.get("rsi", 0),
                "support": analysis.get("support", 0),
                "resistance": analysis.get("resistance", 0),
                "reasons": analysis.get("reasons", []),
                "chart_data": analysis.get("chart_data", {}),
                "buy_score": analysis.get("buy_score", 0),
                "sell_score": analysis.get("sell_score", 0),
            }

            # Update current price for open positions
            if symbol in bot_state["positions"]:
                pos = bot_state["positions"][symbol]
                pos["current_price"] = analysis["price"]
                pos["pnl"] = round((analysis["price"] - pos["entry_price"]) * pos["quantity"], 2)
                pos["pnl_pct"] = round(((analysis["price"] - pos["entry_price"]) / pos["entry_price"]) * 100, 2)

            # Check exit conditions
            should_exit, exit_reason = risk_manager.check_exit_conditions(symbol, analysis["price"])
            if should_exit:
                log(f"EXIT {symbol}: {exit_reason}", "warning")
                execute_sell(symbol, analysis["price"])
                continue

            # Check trade permission
            open_pos = len(bot_state["positions"])
            can_trade, deny = risk_manager.can_trade(
                symbol, analysis["action"], portfolio_value, usdt_available, open_pos
            )

            if analysis["action"] == Signal.BUY and analysis["confidence"] >= 0.35 and can_trade:
                size = risk_manager.calculate_position_size(
                    portfolio_value, usdt_available, analysis["price"],
                    analysis.get("atr", 0), analysis["confidence"]
                )
                if size > 1:
                    execute_buy(symbol, size, analysis["price"])
                    usdt_available -= size

            elif analysis["action"] == Signal.SELL and symbol in bot_state["positions"]:
                execute_sell(symbol, analysis["price"])

        except Exception as e:
            log(f"Error processing {symbol}: {e}", "error")

    bot_state["last_scan"] = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")

    # Update portfolio value
    total = usdt_available
    for pos in bot_state["positions"].values():
        total += pos["current_price"] * pos["quantity"]
    bot_state["portfolio_value"] = round(total, 2)


def bot_loop():
    """Main bot loop running in background thread."""
    log("Bot started")
    while bot_state["running"]:
        try:
            bot_cycle()
            time.sleep(SCAN_INTERVAL_SECONDS)
        except Exception as e:
            log(f"Cycle error: {e}", "error")
            time.sleep(60)
    log("Bot stopped")


# ─── Flask Routes ───────────────────────────────────────────────────

@app.route("/")
def dashboard():
    """Main trading dashboard."""
    return render_template("dashboard.html")


@app.route("/api/status")
def api_status():
    """Get current bot status."""
    progress = (bot_state["portfolio_value"] / bot_state["target"]) * 100
    return jsonify({
        "running": bot_state["running"],
        "mode": bot_state["mode"],
        "portfolio_value": bot_state["portfolio_value"],
        "target": bot_state["target"],
        "progress": round(progress, 1),
        "daily_pnl": round(bot_state["daily_pnl"], 2),
        "total_pnl": round(bot_state["total_pnl"], 2),
        "trades_today": bot_state["trades_today"],
        "total_trades": bot_state["total_trades"],
        "win_rate": round(bot_state["win_rate"], 1),
        "positions": bot_state["positions"],
        "last_scan": bot_state["last_scan"],
        "started_at": bot_state["started_at"],
    })


@app.route("/api/signals")
def api_signals():
    """Get latest signals for all pairs."""
    return jsonify(bot_state["last_signals"])


@app.route("/api/trades")
def api_trades():
    """Get trade history."""
    return jsonify(bot_state["trade_history"][:50])


@app.route("/api/logs")
def api_logs():
    """Get recent log messages."""
    return jsonify(bot_state["log_messages"][:50])


@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    """Run analysis on a specific pair."""
    data = request.get_json()
    symbol = data.get("symbol", "OP/USDT")

    if exchange is None:
        return jsonify({"error": "Exchange not connected"}), 400

    analysis = analyze_pair(symbol)
    bot_state["last_signals"][symbol] = {
        "action": analysis["action"],
        "confidence": analysis["confidence"],
        "price": analysis["price"],
        "rsi": analysis.get("rsi", 0),
        "support": analysis.get("support", 0),
        "resistance": analysis.get("resistance", 0),
        "reasons": analysis.get("reasons", []),
        "chart_data": analysis.get("chart_data", {}),
        "buy_score": analysis.get("buy_score", 0),
        "sell_score": analysis.get("sell_score", 0),
    }
    return jsonify(analysis)


@app.route("/api/start", methods=["POST"])
def api_start():
    """Start the trading bot."""
    global bot_thread

    if bot_state["running"]:
        return jsonify({"status": "already running"})

    data = request.get_json() or {}
    demo = data.get("demo", True)
    bot_state["mode"] = "demo" if demo else "LIVE"

    # Initialize
    init_strategies()
    connected = init_exchange(demo=demo)
    if not connected:
        return jsonify({"error": "Failed to connect to OKX. Check API keys."}), 400

    bot_state["running"] = True
    bot_state["started_at"] = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")

    bot_thread = threading.Thread(target=bot_loop, daemon=True)
    bot_thread.start()

    return jsonify({"status": "started", "mode": bot_state["mode"]})


@app.route("/api/stop", methods=["POST"])
def api_stop():
    """Stop the trading bot."""
    bot_state["running"] = False
    return jsonify({"status": "stopped"})


@app.route("/api/config")
def api_config():
    """Get current bot configuration."""
    return jsonify({
        "pairs": TRADING_PAIRS,
        "initial_capital": INITIAL_CAPITAL,
        "target": TARGET_CAPITAL,
        "risk_per_trade": f"{MAX_RISK_PER_TRADE:.0%}",
        "stop_loss": f"{STOP_LOSS_PCT:.0%}",
        "take_profit": f"{TAKE_PROFIT_PCT:.0%}",
        "trailing_stop": f"{TRAILING_STOP_PCT:.0%}",
        "daily_loss_limit": f"{MAX_DAILY_LOSS_PCT:.0%}",
        "max_positions": MAX_OPEN_POSITIONS,
        "usdt_reserve": MIN_USDT_RESERVE,
        "scan_interval": SCAN_INTERVAL_SECONDS,
        "strategies": {
            "Momentum": MOMENTUM_SETTINGS.get("enabled", True),
            "Bollinger": BOLLINGER_SETTINGS.get("enabled", True),
            "DCA": DCA_SETTINGS.get("enabled", True),
            "Grid": GRID_SETTINGS.get("enabled", True),
        },
    })


if __name__ == "__main__":
    init_strategies()
    app.run(debug=True, host="0.0.0.0", port=5001)
