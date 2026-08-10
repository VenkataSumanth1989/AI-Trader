from unittest import result

from numpy import histogram
import pandas as pd


def calculate_ema(data: pd.DataFrame, period: int) -> pd.Series:
    """
    Calculate Exponential Moving Average.
    """
    return data["Close"].ewm(
        span=period,
        adjust=False
    ).mean()


def calculate_vwap(data: pd.DataFrame) -> pd.Series:
    """
    Calculate session-based intraday VWAP.

    VWAP resets at the beginning of each trading day.
    """

    result = data.copy()

    typical_price = (
        result["High"]
        + result["Low"]
        + result["Close"]
    ) / 3

    price_volume = typical_price * result["Volume"]

    cumulative_price_volume = price_volume.groupby(
        result.index.date
    ).cumsum()

    cumulative_volume = result["Volume"].groupby(
        result.index.date
    ).cumsum()

    return cumulative_price_volume / cumulative_volume

def add_technical_indicators(data: pd.DataFrame) -> pd.DataFrame:
    """
    Add technical indicators to market data.
    """

    result = data.copy()

    result["EMA_9"] = calculate_ema(result, 9)
    result["EMA_20"] = calculate_ema(result, 20)
    result["EMA_50"] = calculate_ema(result, 50)
    result["VWAP"] = calculate_vwap(result)
    result["RSI_14"] = calculate_rsi(result, 14)

    macd, signal, histogram = calculate_macd(result)

    result["MACD"] = macd
    result["MACD_SIGNAL"] = signal
    result["MACD_HISTOGRAM"] = histogram

    result["RELATIVE_VOLUME"] = calculate_relative_volume(result)

    return result
def calculate_rsi(
    data: pd.DataFrame,
    period: int = 14
) -> pd.Series:
    """
    Calculate Relative Strength Index (RSI).
    """

    delta = data["Close"].diff()

    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)

    average_gain = gains.ewm(
        alpha=1 / period,
        adjust=False
    ).mean()

    average_loss = losses.ewm(
        alpha=1 / period,
        adjust=False
    ).mean()

    relative_strength = average_gain / average_loss

    rsi = 100 - (
        100 / (1 + relative_strength)
    )

    return rsi
def calculate_macd(
    data: pd.DataFrame,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
):
    """
    Calculate MACD, Signal Line, and Histogram.
    """

    ema_fast = data["Close"].ewm(
        span=fast_period,
        adjust=False
    ).mean()

    ema_slow = data["Close"].ewm(
        span=slow_period,
        adjust=False
    ).mean()

    macd = ema_fast - ema_slow

    signal = macd.ewm(
        span=signal_period,
        adjust=False
    ).mean()

    histogram = macd - signal

    return macd, signal, histogram
def calculate_relative_volume(
    data: pd.DataFrame,
    period: int = 20
) -> pd.Series:
    """
    Calculate relative volume using the previous candles
    as the baseline.
    """

    average_volume = data["Volume"].rolling(
        window=period
    ).mean().shift(1)

    return data["Volume"] / average_volume