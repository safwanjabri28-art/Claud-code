"""
Trading Strategies
===================
Multiple strategies that generate BUY/SELL/HOLD signals.
The bot combines signals from all active strategies for high-confidence entries.

All strategies are SPOT ONLY -- Sharia compliant.
"""

import pandas as pd

try:
    from trading_bot.indicators import compute_all_indicators, support_resistance, volume_profile
except ImportError:
    from indicators import compute_all_indicators, support_resistance, volume_profile


class Signal:
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

    def __init__(self, action: str, confidence: float, reason: str, strategy: str):
        self.action = action
        self.confidence = confidence  # 0.0 to 1.0
        self.reason = reason
        self.strategy = strategy

    def __repr__(self):
        return f"Signal({self.action}, conf={self.confidence:.0%}, strategy={self.strategy})"


class MomentumStrategy:
    """Trend-following strategy using EMA crossovers + RSI + MACD confirmation."""

    NAME = "Momentum"

    def __init__(self, config: dict):
        self.config = config

    def analyze(self, df: pd.DataFrame) -> Signal:
        if len(df) < 50:
            return Signal(Signal.HOLD, 0, "Insufficient data", self.NAME)

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        confidence = 0.0
        reasons = []

        # ── EMA Crossover ──
        ema_bullish = latest["ema_fast"] > latest["ema_slow"]
        ema_crossed_up = prev["ema_fast"] <= prev["ema_slow"] and ema_bullish
        ema_crossed_down = prev["ema_fast"] >= prev["ema_slow"] and not ema_bullish
        above_trend = latest["close"] > latest["ema_trend"]

        if ema_crossed_up:
            confidence += 0.30
            reasons.append("EMA golden cross (9 > 21)")
        elif ema_crossed_down:
            confidence -= 0.30
            reasons.append("EMA death cross (9 < 21)")

        if above_trend:
            confidence += 0.10
            reasons.append("Price above EMA50 trend")
        else:
            confidence -= 0.10
            reasons.append("Price below EMA50 trend")

        # ── RSI ──
        rsi_val = latest["rsi"]
        if rsi_val < self.config.get("rsi_oversold", 30):
            confidence += 0.25
            reasons.append(f"RSI oversold ({rsi_val:.1f})")
        elif rsi_val > self.config.get("rsi_overbought", 70):
            confidence -= 0.25
            reasons.append(f"RSI overbought ({rsi_val:.1f})")
        elif 40 < rsi_val < 60:
            reasons.append(f"RSI neutral ({rsi_val:.1f})")

        # ── MACD ──
        macd_bullish = latest["macd"] > latest["macd_signal"]
        macd_crossed_up = prev["macd"] <= prev["macd_signal"] and macd_bullish
        macd_hist_rising = latest["macd_hist"] > prev["macd_hist"]

        if macd_crossed_up:
            confidence += 0.20
            reasons.append("MACD bullish crossover")
        elif macd_bullish and macd_hist_rising:
            confidence += 0.10
            reasons.append("MACD histogram expanding")
        elif not macd_bullish:
            confidence -= 0.15
            reasons.append("MACD bearish")

        # ── Volume Confirmation ──
        vol = volume_profile(df["volume"])
        if vol["is_surge"]:
            confidence += 0.15
            reasons.append(f"Volume surge ({vol['ratio']:.1f}x avg)")
        elif vol["is_declining"]:
            confidence -= 0.05
            reasons.append("Volume declining")

        # Determine action
        if confidence >= 0.40:
            return Signal(Signal.BUY, min(confidence, 1.0), " | ".join(reasons), self.NAME)
        elif confidence <= -0.30:
            return Signal(Signal.SELL, min(abs(confidence), 1.0), " | ".join(reasons), self.NAME)
        else:
            return Signal(Signal.HOLD, abs(confidence), " | ".join(reasons), self.NAME)


class BollingerReversionStrategy:
    """Mean reversion using Bollinger Bands -- buy at lower band, sell at upper."""

    NAME = "Bollinger"

    def __init__(self, config: dict):
        self.config = config

    def analyze(self, df: pd.DataFrame) -> Signal:
        if len(df) < 25:
            return Signal(Signal.HOLD, 0, "Insufficient data", self.NAME)

        latest = df.iloc[-1]
        prev = df.iloc[-2]
        price = latest["close"]

        bb_upper = latest["bb_upper"]
        bb_lower = latest["bb_lower"]
        bb_middle = latest["bb_middle"]
        bb_width = (bb_upper - bb_lower) / bb_middle if bb_middle > 0 else 0

        confidence = 0.0
        reasons = []

        # Price position relative to bands
        bb_position = (price - bb_lower) / (bb_upper - bb_lower) if (bb_upper - bb_lower) > 0 else 0.5

        if price <= bb_lower:
            confidence += 0.40
            reasons.append(f"Price at/below lower BB (pos: {bb_position:.2f})")
        elif price <= bb_lower * 1.01:  # Within 1% of lower band
            confidence += 0.25
            reasons.append(f"Price near lower BB (pos: {bb_position:.2f})")
        elif price >= bb_upper:
            confidence -= 0.40
            reasons.append(f"Price at/above upper BB (pos: {bb_position:.2f})")
        elif price >= bb_upper * 0.99:
            confidence -= 0.25
            reasons.append(f"Price near upper BB (pos: {bb_position:.2f})")

        # Bollinger squeeze (low volatility = potential breakout)
        if bb_width < 0.03:
            confidence += 0.10
            reasons.append(f"BB squeeze detected (width: {bb_width:.3f})")

        # RSI confirmation for mean reversion
        rsi_val = latest["rsi"]
        if rsi_val < 35 and confidence > 0:
            confidence += 0.15
            reasons.append(f"RSI confirms oversold ({rsi_val:.1f})")
        elif rsi_val > 65 and confidence < 0:
            confidence -= 0.15
            reasons.append(f"RSI confirms overbought ({rsi_val:.1f})")

        if confidence >= 0.30:
            return Signal(Signal.BUY, min(confidence, 1.0), " | ".join(reasons), self.NAME)
        elif confidence <= -0.30:
            return Signal(Signal.SELL, min(abs(confidence), 1.0), " | ".join(reasons), self.NAME)
        else:
            return Signal(Signal.HOLD, abs(confidence), " | ".join(reasons), self.NAME)


class DCAStrategy:
    """Dollar Cost Averaging on dips -- accumulate when price drops."""

    NAME = "DCA"

    def __init__(self, config: dict):
        self.config = config
        self.dca_levels = {}  # Track DCA entries per symbol

    def analyze(self, df: pd.DataFrame, symbol: str, avg_entry_price: float = 0) -> Signal:
        if len(df) < 20:
            return Signal(Signal.HOLD, 0, "Insufficient data", self.NAME)

        latest = df.iloc[-1]
        price = latest["close"]
        reasons = []
        confidence = 0.0

        # Calculate recent high
        recent_high = df["close"].tail(20).max()
        drop_from_high = (recent_high - price) / recent_high if recent_high > 0 else 0

        dip_threshold = self.config.get("dip_threshold_pct", 0.03)
        max_orders = self.config.get("max_dca_orders", 5)

        current_dca_count = self.dca_levels.get(symbol, 0)

        if drop_from_high >= dip_threshold and current_dca_count < max_orders:
            confidence += 0.20

            # Scale confidence with depth of dip
            if drop_from_high >= dip_threshold * 2:
                confidence += 0.20
                reasons.append(f"Deep dip: {drop_from_high:.1%} from recent high")
            else:
                reasons.append(f"Dip: {drop_from_high:.1%} from recent high")

            # RSI confirmation
            if latest["rsi"] < 35:
                confidence += 0.20
                reasons.append(f"RSI oversold ({latest['rsi']:.1f})")

            # Price below VWAP (institutional value zone)
            if price < latest["vwap"]:
                confidence += 0.10
                reasons.append("Below VWAP")

            reasons.append(f"DCA level {current_dca_count + 1}/{max_orders}")

        if confidence >= 0.30:
            return Signal(Signal.BUY, min(confidence, 1.0), " | ".join(reasons), self.NAME)
        return Signal(Signal.HOLD, confidence, " | ".join(reasons) or "No DCA opportunity", self.NAME)

    def record_dca(self, symbol: str):
        self.dca_levels[symbol] = self.dca_levels.get(symbol, 0) + 1

    def reset_dca(self, symbol: str):
        self.dca_levels[symbol] = 0


class GridStrategy:
    """Grid trading for sideways markets -- places buy/sell orders at intervals."""

    NAME = "Grid"

    def __init__(self, config: dict):
        self.config = config
        self.grids = {}  # Active grid levels per symbol

    def calculate_grid_levels(self, current_price: float, symbol: str) -> dict:
        """Calculate grid buy/sell levels around current price."""
        num_grids = self.config.get("num_grids", 10)
        range_pct = self.config.get("grid_range_pct", 0.15)

        upper = current_price * (1 + range_pct)
        lower = current_price * (1 - range_pct)
        step = (upper - lower) / num_grids

        buy_levels = []
        sell_levels = []

        for i in range(num_grids):
            level = lower + (step * i)
            if level < current_price:
                buy_levels.append(round(level, 6))
            else:
                sell_levels.append(round(level, 6))

        self.grids[symbol] = {
            "buy_levels": buy_levels,
            "sell_levels": sell_levels,
            "upper": upper,
            "lower": lower,
        }
        return self.grids[symbol]

    def analyze(self, df: pd.DataFrame, symbol: str) -> Signal:
        if len(df) < 20:
            return Signal(Signal.HOLD, 0, "Insufficient data", self.NAME)

        price = df["close"].iloc[-1]
        reasons = []

        # Check if market is ranging (low ATR relative to price)
        atr_val = df["atr"].iloc[-1]
        atr_pct = atr_val / price if price > 0 else 0

        # Grid works best in low-volatility sideways markets
        if atr_pct > 0.04:  # Too volatile for grid
            return Signal(Signal.HOLD, 0.1, f"Too volatile for grid (ATR: {atr_pct:.1%})", self.NAME)

        if symbol not in self.grids:
            self.calculate_grid_levels(price, symbol)

        grid = self.grids[symbol]

        # Check if price hit a buy level
        nearest_buy = None
        for level in grid["buy_levels"]:
            if price <= level * 1.005:  # Within 0.5% of buy level
                nearest_buy = level
                break

        nearest_sell = None
        for level in grid["sell_levels"]:
            if price >= level * 0.995:  # Within 0.5% of sell level
                nearest_sell = level
                break

        if nearest_buy:
            reasons.append(f"Hit grid buy level ${nearest_buy:.6f}")
            return Signal(Signal.BUY, 0.50, " | ".join(reasons), self.NAME)
        elif nearest_sell:
            reasons.append(f"Hit grid sell level ${nearest_sell:.6f}")
            return Signal(Signal.SELL, 0.50, " | ".join(reasons), self.NAME)

        return Signal(Signal.HOLD, 0.1, "Between grid levels", self.NAME)


class StrategyEngine:
    """Combines all strategies and produces a weighted final signal."""

    def __init__(self, config: dict):
        momentum_cfg = config.get("momentum", {})
        bollinger_cfg = config.get("bollinger", {})
        dca_cfg = config.get("dca", {})
        grid_cfg = config.get("grid", {})

        self.strategies = []

        if momentum_cfg.get("enabled", True):
            self.strategies.append(("momentum", MomentumStrategy(momentum_cfg), 0.35))
        if bollinger_cfg.get("enabled", True):
            self.strategies.append(("bollinger", BollingerReversionStrategy(bollinger_cfg), 0.25))
        if dca_cfg.get("enabled", True):
            self.dca = DCAStrategy(dca_cfg)
            self.strategies.append(("dca", self.dca, 0.20))
        else:
            self.dca = None
        if grid_cfg.get("enabled", True):
            self.grid = GridStrategy(grid_cfg)
            self.strategies.append(("grid", self.grid, 0.20))
        else:
            self.grid = None

    def analyze(self, df: pd.DataFrame, symbol: str, avg_entry: float = 0) -> dict:
        """Run all strategies and return combined analysis."""
        indicator_config = {
            "momentum": next((s[1].config for s in self.strategies if s[0] == "momentum"), {}),
            "bollinger": next((s[1].config for s in self.strategies if s[0] == "bollinger"), {}),
        }
        df = compute_all_indicators(df, indicator_config)

        signals = []
        for name, strategy, weight in self.strategies:
            if name == "dca":
                signal = strategy.analyze(df, symbol, avg_entry)
            elif name == "grid":
                signal = strategy.analyze(df, symbol)
            else:
                signal = strategy.analyze(df)
            signals.append((signal, weight))

        # Weighted score
        buy_score = 0.0
        sell_score = 0.0
        all_reasons = []

        for signal, weight in signals:
            if signal.action == Signal.BUY:
                buy_score += signal.confidence * weight
            elif signal.action == Signal.SELL:
                sell_score += signal.confidence * weight
            all_reasons.append(f"[{signal.strategy}] {signal.action} ({signal.confidence:.0%}): {signal.reason}")

        # Final decision
        net_score = buy_score - sell_score

        if net_score >= 0.25:
            action = Signal.BUY
            final_confidence = min(buy_score, 1.0)
        elif net_score <= -0.20:
            action = Signal.SELL
            final_confidence = min(sell_score, 1.0)
        else:
            action = Signal.HOLD
            final_confidence = 1.0 - abs(net_score)

        # Support/resistance context
        sr = support_resistance(df["close"])

        return {
            "action": action,
            "confidence": final_confidence,
            "buy_score": buy_score,
            "sell_score": sell_score,
            "net_score": net_score,
            "reasons": all_reasons,
            "price": df["close"].iloc[-1],
            "rsi": df["rsi"].iloc[-1],
            "support": sr["support"],
            "resistance": sr["resistance"],
            "atr": df["atr"].iloc[-1],
            "indicators": {
                "ema_fast": df["ema_fast"].iloc[-1],
                "ema_slow": df["ema_slow"].iloc[-1],
                "ema_trend": df["ema_trend"].iloc[-1],
                "bb_upper": df["bb_upper"].iloc[-1],
                "bb_lower": df["bb_lower"].iloc[-1],
                "macd": df["macd"].iloc[-1],
                "macd_signal": df["macd_signal"].iloc[-1],
                "vwap": df["vwap"].iloc[-1],
            },
        }
