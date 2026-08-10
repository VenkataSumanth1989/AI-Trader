import pandas as pd


def calculate_signal(row: pd.Series) -> dict:
    """
    Calculate a bullish/bearish score from technical indicators.
    """

    score = 0
    reasons = []

    # Price vs VWAP
    if row["Close"] > row["VWAP"]:
        score += 20
        reasons.append("Price above VWAP")

    # EMA 9 vs EMA 20
    if row["EMA_9"] > row["EMA_20"]:
        score += 15
        reasons.append("EMA 9 above EMA 20")

    # EMA 20 vs EMA 50
    if row["EMA_20"] > row["EMA_50"]:
        score += 15
        reasons.append("EMA 20 above EMA 50")

    # RSI
    if row["RSI_14"] > 50:
        score += 10
        reasons.append("RSI above 50")

    # RSI healthy bullish zone
    if 50 < row["RSI_14"] < 70:
        score += 5
        reasons.append("RSI in bullish zone")

    # MACD
    if row["MACD"] > row["MACD_SIGNAL"]:
        score += 15
        reasons.append("MACD above signal")

    # MACD histogram
    if row["MACD_HISTOGRAM"] > 0:
        score += 10
        reasons.append("MACD histogram positive")

    # Relative volume
    if row["RELATIVE_VOLUME"] > 1.5:
        score += 10
        reasons.append("High relative volume")

    # Determine signal
    if score >= 80:
        signal = "STRONG_BULLISH"
    elif score >= 65:
        signal = "BULLISH"
    elif score >= 50:
        signal = "NEUTRAL"
    elif score >= 35:
        signal = "BEARISH"
    else:
        signal = "STRONG_BEARISH"

    return {
        "score": score,
        "signal": signal,
        "reasons": reasons
    }