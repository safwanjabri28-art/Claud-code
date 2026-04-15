#!/usr/bin/env python3
"""
OKX Halal Spot Trading Bot
============================
Sharia-compliant: SPOT ONLY, no leverage, no futures, no interest.

Strategies: Momentum + Bollinger Reversion + DCA + Grid
Risk: Stop-loss, trailing stop, daily limits, position sizing

Usage:
    python bot.py              # Run the bot
    python bot.py --backtest   # Run backtest on historical data
    python bot.py --analyze    # One-time analysis without trading
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import ccxt
import pandas as pd

from config import (
    BOLLINGER_SETTINGS,
    DCA_SETTINGS,
    GRID_SETTINGS,
    INITIAL_CAPITAL,
    LOG_FILE,
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
from risk_manager import RiskManager
from strategies import Signal, StrategyEngine

# ─── Logging Setup ──────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE),
    ],
)
logger = logging.getLogger("trading_bot")

BANNER = """
╔══════════════════════════════════════════════════════════════╗
║           OKX HALAL SPOT TRADING BOT                        ║
║      Sharia Compliant: No Leverage | No Futures | Spot Only ║
╠══════════════════════════════════════════════════════════════╣
║  Strategies: Momentum | Bollinger | DCA | Grid              ║
║  Risk: Stop-Loss | Trailing Stop | Daily Limits             ║
╚══════════════════════════════════════════════════════════════╝
"""


class TradingBot:
    """Main trading bot class."""

    def __init__(self, demo: bool = True):
        self.demo = demo
        self.exchange = self._connect_exchange()
        self.strategy_engine = StrategyEngine({
            "momentum": {**MOMENTUM_SETTINGS, "enabled": MOMENTUM_SETTINGS.get("enabled", True)},
            "bollinger": {**BOLLINGER_SETTINGS, "enabled": BOLLINGER_SETTINGS.get("enabled", True)},
            "dca": {**DCA_SETTINGS, "enabled": DCA_SETTINGS.get("enabled", True)},
            "grid": {**GRID_SETTINGS, "enabled": GRID_SETTINGS.get("enabled", True)},
        })
        self.risk_manager = RiskManager({
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
        self.trade_history = self._load_trade_history()
        self.running = False

    def _connect_exchange(self) -> ccxt.okx:
        """Connect to OKX exchange."""
        config = {
            "apiKey": OKX_API_KEY,
            "secret": OKX_SECRET_KEY,
            "password": OKX_PASSPHRASE,
            "enableRateLimit": True,
            "options": {"defaultType": "spot"},  # SPOT ONLY - Halal
        }

        if self.demo:
            config["sandbox"] = True
            logger.info("DEMO MODE: Using OKX paper trading")

        exchange = ccxt.okx(config)

        try:
            exchange.load_markets()
            logger.info(f"Connected to OKX ({'Demo' if self.demo else 'Live'})")
        except Exception as e:
            logger.error(f"Failed to connect to OKX: {e}")
            logger.info("Running in analysis-only mode (no API connection)")

        return exchange

    def _load_trade_history(self) -> list:
        """Load trade history from file."""
        path = Path(TRADE_HISTORY_FILE)
        if path.exists():
            with open(path) as f:
                return json.load(f)
        return []

    def _save_trade_history(self):
        """Save trade history to file."""
        with open(TRADE_HISTORY_FILE, "w") as f:
            json.dump(self.trade_history, f, indent=2, default=str)

    def fetch_ohlcv(self, symbol: str, timeframe: str = "15m", limit: int = 100) -> pd.DataFrame:
        """Fetch OHLCV candle data from OKX."""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            df.set_index("timestamp", inplace=True)
            return df
        except Exception as e:
            logger.error(f"Error fetching OHLCV for {symbol}: {e}")
            return pd.DataFrame()

    def get_balance(self) -> dict:
        """Get current USDT and token balances."""
        try:
            balance = self.exchange.fetch_balance()
            usdt = balance.get("USDT", {}).get("free", 0)
            total = balance.get("USDT", {}).get("total", 0)

            holdings = {}
            for symbol in TRADING_PAIRS:
                token = symbol.split("/")[0]
                holdings[token] = {
                    "free": balance.get(token, {}).get("free", 0),
                    "total": balance.get(token, {}).get("total", 0),
                }

            return {
                "usdt_free": usdt,
                "usdt_total": total,
                "holdings": holdings,
            }
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return {"usdt_free": 0, "usdt_total": 0, "holdings": {}}

    def get_portfolio_value(self) -> float:
        """Calculate total portfolio value in USDT."""
        balance = self.get_balance()
        total = balance["usdt_total"]

        for symbol in TRADING_PAIRS:
            token = symbol.split("/")[0]
            amount = balance["holdings"].get(token, {}).get("total", 0)
            if amount > 0:
                try:
                    ticker = self.exchange.fetch_ticker(symbol)
                    total += amount * ticker["last"]
                except Exception:
                    pass

        return total

    def execute_buy(self, symbol: str, usdt_amount: float, price: float) -> dict | None:
        """Execute a spot BUY order."""
        try:
            token = symbol.split("/")[0]
            quantity = usdt_amount / price

            # Get market info for minimum order size
            market = self.exchange.market(symbol)
            min_amount = market.get("limits", {}).get("amount", {}).get("min", 0)
            min_cost = market.get("limits", {}).get("cost", {}).get("min", 0)

            if quantity < min_amount:
                logger.warning(f"Order too small: {quantity} < min {min_amount} {token}")
                return None
            if usdt_amount < min_cost:
                logger.warning(f"Order cost too small: ${usdt_amount:.2f} < min ${min_cost}")
                return None

            logger.info(f"BUYING {quantity:.4f} {token} @ ${price:.6f} = ${usdt_amount:.2f}")

            if self.demo:
                order = {"id": f"demo_{int(time.time())}", "status": "filled",
                         "filled": quantity, "price": price}
            else:
                order = self.exchange.create_market_buy_order(symbol, quantity)

            # Record trade
            trade = {
                "time": datetime.now(timezone.utc).isoformat(),
                "symbol": symbol,
                "action": "BUY",
                "price": price,
                "quantity": quantity,
                "value": usdt_amount,
                "order_id": order.get("id"),
            }
            self.trade_history.append(trade)
            self._save_trade_history()

            self.risk_manager.record_trade(symbol, "BUY", price, quantity)
            logger.info(f"BUY FILLED: {quantity:.4f} {token} @ ${price:.6f}")

            return trade

        except Exception as e:
            logger.error(f"Buy order failed for {symbol}: {e}")
            return None

    def execute_sell(self, symbol: str, quantity: float, price: float,
                     entry_price: float) -> dict | None:
        """Execute a spot SELL order."""
        try:
            token = symbol.split("/")[0]
            value = quantity * price
            pnl = (price - entry_price) * quantity
            pnl_pct = (price - entry_price) / entry_price * 100

            logger.info(f"SELLING {quantity:.4f} {token} @ ${price:.6f} "
                        f"= ${value:.2f} (PnL: ${pnl:.2f} / {pnl_pct:+.1f}%)")

            if self.demo:
                order = {"id": f"demo_{int(time.time())}", "status": "filled",
                         "filled": quantity, "price": price}
            else:
                order = self.exchange.create_market_sell_order(symbol, quantity)

            trade = {
                "time": datetime.now(timezone.utc).isoformat(),
                "symbol": symbol,
                "action": "SELL",
                "price": price,
                "quantity": quantity,
                "value": value,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "order_id": order.get("id"),
            }
            self.trade_history.append(trade)
            self._save_trade_history()

            self.risk_manager.record_trade(symbol, "SELL", price, quantity, pnl)
            emoji = "+" if pnl >= 0 else ""
            logger.info(f"SELL FILLED: {quantity:.4f} {token} | PnL: {emoji}${pnl:.2f} ({pnl_pct:+.1f}%)")

            return trade

        except Exception as e:
            logger.error(f"Sell order failed for {symbol}: {e}")
            return None

    def analyze_pair(self, symbol: str) -> dict:
        """Run full analysis on a trading pair."""
        # Fetch data for multiple timeframes
        df_primary = self.fetch_ohlcv(symbol, PRIMARY_TIMEFRAME, 100)
        df_secondary = self.fetch_ohlcv(symbol, SECONDARY_TIMEFRAME, 100)
        df_trend = self.fetch_ohlcv(symbol, TREND_TIMEFRAME, 100)

        if df_primary.empty:
            return {"action": Signal.HOLD, "confidence": 0, "reasons": ["No data"]}

        # Primary analysis
        analysis = self.strategy_engine.analyze(df_primary, symbol)

        # Multi-timeframe confirmation
        if not df_secondary.empty:
            secondary = self.strategy_engine.analyze(df_secondary, symbol)
            # Boost confidence if higher timeframe agrees
            if secondary["action"] == analysis["action"]:
                analysis["confidence"] = min(analysis["confidence"] * 1.2, 1.0)
                analysis["reasons"].append(f"[MTF] {SECONDARY_TIMEFRAME} confirms {analysis['action']}")
            elif secondary["action"] != Signal.HOLD and secondary["action"] != analysis["action"]:
                analysis["confidence"] *= 0.7
                analysis["reasons"].append(f"[MTF] {SECONDARY_TIMEFRAME} disagrees: {secondary['action']}")

        # Trend filter from higher timeframe
        if not df_trend.empty:
            trend = self.strategy_engine.analyze(df_trend, symbol)
            if analysis["action"] == Signal.BUY and trend["action"] == Signal.SELL:
                analysis["confidence"] *= 0.5
                analysis["reasons"].append(f"[TREND] {TREND_TIMEFRAME} bearish - reduced confidence")

        return analysis

    def process_pair(self, symbol: str, portfolio_value: float, usdt_balance: float):
        """Process a single trading pair -- analyze and potentially trade."""
        analysis = self.analyze_pair(symbol)

        price = analysis["price"]
        action = analysis["action"]
        confidence = analysis["confidence"]
        reasons = analysis["reasons"]

        logger.info(f"\n{'─'*50}")
        logger.info(f"  {symbol} | Price: ${price:.6f} | RSI: {analysis['rsi']:.1f}")
        logger.info(f"  Action: {action} | Confidence: {confidence:.0%}")
        logger.info(f"  Support: ${analysis['support']:.6f} | Resistance: ${analysis['resistance']:.6f}")
        for r in reasons:
            logger.info(f"    {r}")

        # Check exit conditions for existing positions
        should_exit, exit_reason = self.risk_manager.check_exit_conditions(symbol, price)
        if should_exit:
            pos = self.risk_manager.positions[symbol]
            logger.info(f"  EXIT SIGNAL: {exit_reason}")
            self.execute_sell(symbol, pos["quantity"], price, pos["entry_price"])
            return

        # Check if we can trade
        open_positions = len(self.risk_manager.positions)
        can_trade, deny_reason = self.risk_manager.can_trade(
            symbol, action, portfolio_value, usdt_balance, open_positions
        )

        if not can_trade:
            logger.info(f"  Trade blocked: {deny_reason}")
            return

        # Execute trade
        if action == Signal.BUY and confidence >= 0.35:
            size = self.risk_manager.calculate_position_size(
                portfolio_value, usdt_balance, price,
                analysis["atr"], confidence
            )
            if size > 0:
                self.execute_buy(symbol, size, price)
            else:
                logger.info(f"  Position size too small, skipping")

        elif action == Signal.SELL and symbol in self.risk_manager.positions:
            pos = self.risk_manager.positions[symbol]
            self.execute_sell(symbol, pos["quantity"], price, pos["entry_price"])

    def run_cycle(self):
        """Run one analysis + trading cycle for all pairs."""
        portfolio_value = self.get_portfolio_value()
        balance = self.get_balance()
        usdt = balance["usdt_free"]

        progress = (portfolio_value / TARGET_CAPITAL) * 100 if portfolio_value > 0 else 0

        logger.info(f"\n{'='*60}")
        logger.info(f"  CYCLE @ {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        logger.info(f"  Portfolio: ${portfolio_value:.2f} / ${TARGET_CAPITAL:,.0f} ({progress:.1f}%)")
        logger.info(f"  USDT Available: ${usdt:.2f}")
        logger.info(f"  Daily PnL: ${self.risk_manager.daily_pnl:+.2f}")
        logger.info(f"{'='*60}")

        if portfolio_value >= TARGET_CAPITAL:
            logger.info("TARGET REACHED! Stopping bot.")
            self.running = False
            return

        for symbol in TRADING_PAIRS:
            try:
                self.process_pair(symbol, portfolio_value, usdt)
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")

        # Status summary
        status = self.risk_manager.get_portfolio_status()
        logger.info(f"\n  Open positions: {status['open_positions']}")
        logger.info(f"  Trades today: {status['trade_count']}")
        logger.info(f"  Daily PnL: ${status['daily_pnl']:+.2f}")

    def run(self):
        """Main bot loop."""
        print(BANNER)
        logger.info("Bot starting...")
        logger.info(f"Target: ${INITIAL_CAPITAL:.2f} -> ${TARGET_CAPITAL:,}")
        logger.info(f"Pairs: {', '.join(TRADING_PAIRS)}")
        logger.info(f"Mode: {'DEMO' if self.demo else 'LIVE'}")

        self.running = True
        portfolio_value = self.get_portfolio_value()
        self.risk_manager.reset_daily(portfolio_value)

        while self.running:
            try:
                self.run_cycle()
                logger.info(f"\nNext scan in {SCAN_INTERVAL_SECONDS}s...")
                time.sleep(SCAN_INTERVAL_SECONDS)
            except KeyboardInterrupt:
                logger.info("\nBot stopped by user.")
                break
            except Exception as e:
                logger.error(f"Cycle error: {e}")
                time.sleep(60)  # Wait a minute before retrying

        self.print_summary()

    def analyze_only(self):
        """Run analysis without trading."""
        print(BANNER)
        logger.info("ANALYSIS MODE (no trades will be executed)\n")

        for symbol in TRADING_PAIRS:
            analysis = self.analyze_pair(symbol)
            print(f"\n{'='*55}")
            print(f"  {symbol}")
            print(f"{'='*55}")
            print(f"  Price:       ${analysis['price']:.6f}")
            print(f"  Action:      {analysis['action']}")
            print(f"  Confidence:  {analysis['confidence']:.0%}")
            print(f"  RSI:         {analysis['rsi']:.1f}")
            print(f"  Support:     ${analysis['support']:.6f}")
            print(f"  Resistance:  ${analysis['resistance']:.6f}")
            print(f"  Buy Score:   {analysis['buy_score']:.2f}")
            print(f"  Sell Score:  {analysis['sell_score']:.2f}")
            print(f"  Net Score:   {analysis['net_score']:+.2f}")
            print(f"\n  Indicators:")
            for k, v in analysis["indicators"].items():
                print(f"    {k:15s}: {v:.6f}")
            print(f"\n  Signals:")
            for r in analysis["reasons"]:
                print(f"    {r}")

    def print_summary(self):
        """Print trading session summary."""
        if not self.trade_history:
            print("\nNo trades executed.")
            return

        total_pnl = sum(t.get("pnl", 0) for t in self.trade_history)
        wins = sum(1 for t in self.trade_history if t.get("pnl", 0) > 0)
        losses = sum(1 for t in self.trade_history if t.get("pnl", 0) < 0)
        total_trades = len([t for t in self.trade_history if "pnl" in t])
        win_rate = wins / total_trades * 100 if total_trades > 0 else 0

        print(f"\n{'='*55}")
        print(f"  SESSION SUMMARY")
        print(f"{'='*55}")
        print(f"  Total Trades:  {len(self.trade_history)}")
        print(f"  Wins:          {wins}")
        print(f"  Losses:        {losses}")
        print(f"  Win Rate:      {win_rate:.1f}%")
        print(f"  Total PnL:     ${total_pnl:+.2f}")
        print(f"{'='*55}")


def main():
    parser = argparse.ArgumentParser(description="OKX Halal Spot Trading Bot")
    parser.add_argument("--backtest", action="store_true", help="Run backtest")
    parser.add_argument("--analyze", action="store_true", help="Analysis only, no trading")
    parser.add_argument("--live", action="store_true", help="Live trading (default: demo)")
    args = parser.parse_args()

    demo = not args.live

    if args.live:
        logger.warning("LIVE TRADING MODE - Real money will be used!")
        confirm = input("Type 'YES' to confirm live trading: ")
        if confirm != "YES":
            logger.info("Cancelled.")
            return

    bot = TradingBot(demo=demo)

    if args.analyze:
        bot.analyze_only()
    else:
        bot.run()


if __name__ == "__main__":
    main()
