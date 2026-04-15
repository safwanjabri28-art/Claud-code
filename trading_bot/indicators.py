"""
Technical Analysis Indicators
==============================
Pure numpy/pandas implementations for speed.
"""

import numpy as np
import pandas as pd


def ema(series: pd.Series, period: int) -> pd.Series:
    """Exponential Moving Average."""
    return series.ewm(span=period, adjust=False).mean()


def sma(series: pd.Series, period: int) -> pd.Series:
    """Simple Moving Average."""
    return series.rolling(window=period).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.ewm(alpha=1 / period, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period).mean()

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """MACD indicator. Returns (macd_line, signal_line, histogram)."""
    ema_fast = ema(series, fast)
    ema_slow = ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def bollinger_bands(series: pd.Series, period: int = 20, std_dev: float = 2.0):
    """Bollinger Bands. Returns (upper, middle, lower)."""
    middle = sma(series, period)
    std = series.rolling(window=period).std()
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    return upper, middle, lower


def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Average True Range -- measures volatility."""
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return true_range.rolling(window=period).mean()


def vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
    """Volume Weighted Average Price."""
    typical_price = (high + low + close) / 3
    cumulative_tp_vol = (typical_price * volume).cumsum()
    cumulative_vol = volume.cumsum()
    return cumulative_tp_vol / cumulative_vol


def support_resistance(close: pd.Series, window: int = 20):
    """Find recent support and resistance levels."""
    recent = close.tail(window)
    support = recent.min()
    resistance = recent.max()
    pivot = (support + resistance + close.iloc[-1]) / 3
    return {
        "support": support,
        "resistance": resistance,
        "pivot": pivot,
        "s1": (2 * pivot) - resistance,
        "r1": (2 * pivot) - support,
    }


def volume_profile(volume: pd.Series, period: int = 20) -> dict:
    """Analyze volume trend."""
    recent_vol = volume.tail(period)
    avg_vol = recent_vol.mean()
    current_vol = volume.iloc[-1]
    return {
        "current": current_vol,
        "average": avg_vol,
        "ratio": current_vol / avg_vol if avg_vol > 0 else 0,
        "is_surge": current_vol > avg_vol * 1.5,
        "is_declining": current_vol < avg_vol * 0.7,
    }


def compute_all_indicators(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """Compute all indicators on an OHLCV dataframe.

    Expects columns: open, high, low, close, volume
    """
    mom = config.get("momentum", {})
    boll = config.get("bollinger", {})

    # EMAs
    df["ema_fast"] = ema(df["close"], mom.get("ema_fast", 9))
    df["ema_slow"] = ema(df["close"], mom.get("ema_slow", 21))
    df["ema_trend"] = ema(df["close"], mom.get("ema_trend", 50))

    # RSI
    df["rsi"] = rsi(df["close"], mom.get("rsi_period", 14))

    # MACD
    df["macd"], df["macd_signal"], df["macd_hist"] = macd(
        df["close"],
        mom.get("macd_fast", 12),
        mom.get("macd_slow", 26),
        mom.get("macd_signal", 9),
    )

    # Bollinger Bands
    df["bb_upper"], df["bb_middle"], df["bb_lower"] = bollinger_bands(
        df["close"],
        boll.get("period", 20),
        boll.get("std_dev", 2.0),
    )

    # ATR (volatility)
    df["atr"] = atr(df["high"], df["low"], df["close"])

    # VWAP
    df["vwap"] = vwap(df["high"], df["low"], df["close"], df["volume"])

    # Volume moving average
    df["vol_sma"] = sma(df["volume"], 20)
    df["vol_ratio"] = df["volume"] / df["vol_sma"]

    return df
