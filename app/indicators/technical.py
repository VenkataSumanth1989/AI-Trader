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

    return result