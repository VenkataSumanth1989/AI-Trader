import pandas as pd


def add_trend_indicators(data: pd.DataFrame) -> pd.DataFrame:
    """
    Add long-term trend indicators using daily price data.

    SMA 50  = 50-day simple moving average
    SMA 200 = 200-day simple moving average
    """

    data = data.copy()

    data["SMA_50"] = data["Close"].rolling(window=50).mean()
    data["SMA_200"] = data["Close"].rolling(window=200).mean()

    return data


def determine_market_regime(row: pd.Series) -> str:
    """
    Determine long-term market regime.

    BULLISH:
        Price > SMA 200
        AND SMA 50 > SMA 200

    BEARISH:
        Price < SMA 200
        AND SMA 50 < SMA 200

    Otherwise:
        NEUTRAL
    """

    if pd.isna(row["SMA_50"]) or pd.isna(row["SMA_200"]):
        return "UNKNOWN"

    if (
        row["Close"] > row["SMA_200"]
        and row["SMA_50"] > row["SMA_200"]
    ):
        return "BULLISH"

    if (
        row["Close"] < row["SMA_200"]
        and row["SMA_50"] < row["SMA_200"]
    ):
        return "BEARISH"

    return "NEUTRAL"