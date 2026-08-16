import pandas as pd


def add_bollinger_bands(
    data: pd.DataFrame,
    period: int = 20,
    std_dev: float = 2.0,
) -> pd.DataFrame:
    """
    Add Bollinger Bands to price data.

    Middle Band:
        20-period SMA

    Upper Band:
        Middle Band + 2 standard deviations

    Lower Band:
        Middle Band - 2 standard deviations

    Also calculates:
        BB_WIDTH
        BB_PERCENT_B
    """

    result = data.copy()

    middle_band = (
        result["Close"]
        .rolling(window=period)
        .mean()
    )

    rolling_std = (
        result["Close"]
        .rolling(window=period)
        .std()
    )

    upper_band = (
        middle_band
        + std_dev * rolling_std
    )

    lower_band = (
        middle_band
        - std_dev * rolling_std
    )

    result["BB_MIDDLE"] = middle_band
    result["BB_UPPER"] = upper_band
    result["BB_LOWER"] = lower_band

    # --------------------------------------------------
    # BAND WIDTH
    # --------------------------------------------------

    result["BB_WIDTH"] = (
        (upper_band - lower_band)
        / middle_band
        * 100
    )

    # --------------------------------------------------
    # %B
    #
    # 0   = at lower band
    # 0.5 = at middle band
    # 1   = at upper band
    # --------------------------------------------------

    band_range = (
        upper_band
        - lower_band
    )

    result["BB_PERCENT_B"] = (
        (result["Close"] - lower_band)
        / band_range
    )

    return result


def analyze_bollinger_bands(
    row: pd.Series,
) -> dict:
    """
    Interpret the latest Bollinger Band values.

    This function does not place trades.
    """

    required = [
        "Close",
        "BB_MIDDLE",
        "BB_UPPER",
        "BB_LOWER",
        "BB_WIDTH",
        "BB_PERCENT_B",
    ]

    for column in required:

        if column not in row.index:
            return {
                "signal": "UNKNOWN",
                "position": "UNKNOWN",
                "confidence": 0,
                "reasons": [
                    "Bollinger Band data unavailable"
                ],
                "warnings": [],
            }

        if pd.isna(row[column]):
            return {
                "signal": "UNKNOWN",
                "position": "UNKNOWN",
                "confidence": 0,
                "reasons": [
                    "Bollinger Band values not ready"
                ],
                "warnings": [],
            }

    close = float(row["Close"])
    middle = float(row["BB_MIDDLE"])
    upper = float(row["BB_UPPER"])
    lower = float(row["BB_LOWER"])
    width = float(row["BB_WIDTH"])
    percent_b = float(row["BB_PERCENT_B"])

    reasons = []
    warnings = []

    # --------------------------------------------------
    # PRICE LOCATION
    # --------------------------------------------------

    if close > upper:

        position = "ABOVE_UPPER_BAND"

        reasons.append(
            "Price is above the upper Bollinger Band"
        )

        warnings.append(
            "Price may be extended above its recent range"
        )

    elif close < lower:

        position = "BELOW_LOWER_BAND"

        reasons.append(
            "Price is below the lower Bollinger Band"
        )

        warnings.append(
            "Price may be extended below its recent range"
        )

    elif close >= middle:

        position = "UPPER_HALF"

        reasons.append(
            "Price is above the Bollinger middle band"
        )

    else:

        position = "LOWER_HALF"

        reasons.append(
            "Price is below the Bollinger middle band"
        )

    # --------------------------------------------------
    # SIGNAL
    # --------------------------------------------------

    if percent_b >= 1:

        signal = "STRONG_UPPER_EXTENSION"

        confidence = 70

    elif percent_b >= 0.80:

        signal = "BULLISH_PRESSURE"

        confidence = 65

    elif percent_b >= 0.55:

        signal = "MILD_BULLISH"

        confidence = 55

    elif percent_b <= 0:

        signal = "STRONG_LOWER_EXTENSION"

        confidence = 70

    elif percent_b <= 0.20:

        signal = "BEARISH_PRESSURE"

        confidence = 65

    elif percent_b <= 0.45:

        signal = "MILD_BEARISH"

        confidence = 55

    else:

        signal = "NEUTRAL"

        confidence = 50

    # --------------------------------------------------
    # VOLATILITY
    # --------------------------------------------------

    if width < 2:

        warnings.append(
            "Bollinger Bands are narrow; volatility is compressed"
        )

    elif width > 8:

        warnings.append(
            "Bollinger Bands are wide; volatility is elevated"
        )

    return {
        "signal": signal,
        "position": position,
        "confidence": confidence,
        "middle": middle,
        "upper": upper,
        "lower": lower,
        "width": width,
        "percent_b": percent_b,
        "reasons": reasons,
        "warnings": warnings,
    }