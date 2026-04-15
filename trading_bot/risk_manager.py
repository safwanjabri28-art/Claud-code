"""
Risk Management Module
=======================
Protects capital with strict rules. This is the most important module.
"""

import time
import logging

logger = logging.getLogger("trading_bot")


class RiskManager:
    """Enforces risk limits to protect your capital."""

    def __init__(self, config: dict):
        self.max_risk_per_trade = config.get("max_risk_per_trade", 0.02)
        self.max_allocation = config.get("max_allocation_per_token", 0.40)
        self.stop_loss_pct = config.get("stop_loss_pct", 0.05)
        self.take_profit_pct = config.get("take_profit_pct", 0.08)
        self.trailing_stop_pct = config.get("trailing_stop_pct", 0.03)
        self.max_daily_loss_pct = config.get("max_daily_loss_pct", 0.05)
        self.max_open_positions = config.get("max_open_positions", 3)
        self.min_usdt_reserve = config.get("min_usdt_reserve", 50.0)
        self.loss_cooldown = config.get("loss_cooldown_seconds", 300)

        self.daily_pnl = 0.0
        self.daily_start_balance = 0.0
        self.last_loss_time = 0
        self.trade_count_today = 0
        self.positions = {}  # symbol -> position info

    def reset_daily(self, current_balance: float):
        """Reset daily counters."""
        self.daily_pnl = 0.0
        self.daily_start_balance = current_balance
        self.trade_count_today = 0
        logger.info(f"Daily reset. Starting balance: ${current_balance:.2f}")

    def can_trade(self, symbol: str, action: str, portfolio_value: float,
                  usdt_balance: float, current_positions: int) -> tuple[bool, str]:
        """Check if a trade is allowed under risk rules."""

        # Daily loss limit
        if self.daily_start_balance > 0:
            daily_loss_ratio = -self.daily_pnl / self.daily_start_balance
            if daily_loss_ratio >= self.max_daily_loss_pct:
                return False, f"Daily loss limit reached ({daily_loss_ratio:.1%})"

        # Cooldown after loss
        if time.time() - self.last_loss_time < self.loss_cooldown:
            remaining = self.loss_cooldown - (time.time() - self.last_loss_time)
            return False, f"Loss cooldown active ({remaining:.0f}s remaining)"

        if action == "BUY":
            # Max positions check
            if current_positions >= self.max_open_positions:
                return False, f"Max positions reached ({self.max_open_positions})"

            # USDT reserve check
            if usdt_balance <= self.min_usdt_reserve:
                return False, f"USDT below reserve (${usdt_balance:.2f} <= ${self.min_usdt_reserve})"

            # Max allocation per token
            if symbol in self.positions:
                pos_value = self.positions[symbol].get("value", 0)
                if portfolio_value > 0 and pos_value / portfolio_value >= self.max_allocation:
                    return False, f"Max allocation for {symbol} reached ({self.max_allocation:.0%})"

        return True, "OK"

    def calculate_position_size(self, portfolio_value: float, usdt_available: float,
                                price: float, atr: float, confidence: float) -> float:
        """Calculate optimal position size based on risk parameters."""
        # Base size from risk per trade
        risk_amount = portfolio_value * self.max_risk_per_trade

        # ATR-based sizing: smaller positions in volatile markets
        if atr > 0 and price > 0:
            atr_pct = atr / price
            # Reduce size when volatility is high
            volatility_factor = max(0.5, min(1.5, 0.02 / atr_pct))
        else:
            volatility_factor = 1.0

        # Confidence scaling: higher confidence = larger position
        confidence_factor = 0.5 + (confidence * 0.5)  # Range: 0.5 to 1.0

        # Calculate size
        position_size = risk_amount * volatility_factor * confidence_factor

        # Cap at available USDT minus reserve
        max_available = usdt_available - self.min_usdt_reserve
        position_size = min(position_size, max_available)

        # Cap at max allocation
        max_alloc_size = portfolio_value * self.max_allocation
        position_size = min(position_size, max_alloc_size)

        # Ensure positive
        return max(0, position_size)

    def get_stop_loss_price(self, entry_price: float, side: str = "long") -> float:
        """Calculate stop-loss price."""
        if side == "long":
            return entry_price * (1 - self.stop_loss_pct)
        return entry_price * (1 + self.stop_loss_pct)

    def get_take_profit_price(self, entry_price: float, side: str = "long") -> float:
        """Calculate take-profit price."""
        if side == "long":
            return entry_price * (1 + self.take_profit_pct)
        return entry_price * (1 - self.take_profit_pct)

    def check_exit_conditions(self, symbol: str, current_price: float) -> tuple[bool, str]:
        """Check if any open position should be exited."""
        if symbol not in self.positions:
            return False, ""

        pos = self.positions[symbol]
        entry = pos["entry_price"]
        highest = pos.get("highest_price", entry)

        pnl_pct = (current_price - entry) / entry

        # Stop-loss hit
        if pnl_pct <= -self.stop_loss_pct:
            return True, f"Stop-loss triggered ({pnl_pct:.1%})"

        # Take-profit hit
        if pnl_pct >= self.take_profit_pct:
            # Activate trailing stop
            trailing_stop = highest * (1 - self.trailing_stop_pct)
            if current_price <= trailing_stop:
                return True, f"Trailing stop triggered (from peak ${highest:.6f})"

            # Update highest price
            if current_price > highest:
                self.positions[symbol]["highest_price"] = current_price

        return False, ""

    def record_trade(self, symbol: str, action: str, price: float,
                     quantity: float, pnl: float = 0):
        """Record a trade for risk tracking."""
        if action == "BUY":
            self.positions[symbol] = {
                "entry_price": price,
                "quantity": quantity,
                "value": price * quantity,
                "highest_price": price,
                "entry_time": time.time(),
            }
        elif action == "SELL":
            self.daily_pnl += pnl
            if pnl < 0:
                self.last_loss_time = time.time()
            if symbol in self.positions:
                del self.positions[symbol]

        self.trade_count_today += 1

    def get_portfolio_status(self) -> dict:
        """Get current risk status summary."""
        return {
            "daily_pnl": self.daily_pnl,
            "trade_count": self.trade_count_today,
            "open_positions": len(self.positions),
            "positions": {s: p for s, p in self.positions.items()},
            "in_cooldown": time.time() - self.last_loss_time < self.loss_cooldown,
        }
