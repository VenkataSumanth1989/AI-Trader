import pandas as pd


def detect_rsi_divergence(
    data: pd.DataFrame,
    lookback: int = 60,
    swing_window: int = 3,
) -> dict:
    """
    Detect regular RSI divergence using confirmed swing points.

    Bullish divergence:
        Price makes a lower low
        RSI makes a higher low

    Bearish divergence:
        Price makes a higher high
        RSI makes a lower high
    """

    result = {
        "divergence": "NONE",
        "direction": "NEUTRAL",
        "confidence": 0,
        "price_point_1": None,
        "price_point_2": None,
        "rsi_point_1": None,
        "rsi_point_2": None,
        "reasons": [],
    }

    # --------------------------------------------------
    # VALIDATION
    # --------------------------------------------------

    required_columns = {
        "Close",
        "High",
        "Low",
        "RSI_14",
    }

    if not required_columns.issubset(data.columns):
        result["reasons"].append(
            "Required RSI divergence data is missing"
        )
        return result

    df = data[
        ["Close", "High", "Low", "RSI_14"]
    ].dropna().copy()

    if len(df) < 20:
        result["reasons"].append(
            "Not enough data for RSI divergence detection"
        )
        return result

    df = df.tail(lookback)

    # --------------------------------------------------
    # FIND SWING LOWS / HIGHS
    # --------------------------------------------------

    swing_lows = []
    swing_highs = []

    for i in range(
        swing_window,
        len(df) - swing_window,
    ):

        current_low = df["Low"].iloc[i]

        low_window = df["Low"].iloc[
            i - swing_window:
            i + swing_window + 1
        ]

        if current_low == low_window.min():
            swing_lows.append(i)

        current_high = df["High"].iloc[i]

        high_window = df["High"].iloc[
            i - swing_window:
            i + swing_window + 1
        ]

        if current_high == high_window.max():
            swing_highs.append(i)

    bullish_candidate = None
    bearish_candidate = None

    # --------------------------------------------------
    # REGULAR BULLISH DIVERGENCE
    # --------------------------------------------------

    if len(swing_lows) >= 2:

        first = swing_lows[-2]
        second = swing_lows[-1]

        price_1 = float(
            df["Low"].iloc[first]
        )

        price_2 = float(
            df["Low"].iloc[second]
        )

        rsi_1 = float(
            df["RSI_14"].iloc[first]
        )

        rsi_2 = float(
            df["RSI_14"].iloc[second]
        )

        if (
            price_2 < price_1
            and rsi_2 > rsi_1
        ):

            price_change = abs(
                (price_2 - price_1)
                / price_1
                * 100
            )

            rsi_change = (
                rsi_2 - rsi_1
            )

            score = 50

            if price_change >= 0.5:
                score += 10

            if price_change >= 1.0:
                score += 10

            if rsi_change >= 3:
                score += 10

            if rsi_change >= 5:
                score += 10

            if rsi_1 <= 35:
                score += 10

            bullish_candidate = {
                "divergence": "REGULAR_BULLISH",
                "direction": "BULLISH",
                "confidence": min(
                    score,
                    100,
                ),
                "price_point_1": price_1,
                "price_point_2": price_2,
                "rsi_point_1": rsi_1,
                "rsi_point_2": rsi_2,
                "time_point_1": df.index[first],
                "time_point_2": df.index[second],
                "reasons": [
                    "Price formed a lower swing low",
                    "RSI formed a higher swing low",
                ],
            }

    # --------------------------------------------------
    # REGULAR BEARISH DIVERGENCE
    # --------------------------------------------------

    if len(swing_highs) >= 2:

        first = swing_highs[-2]
        second = swing_highs[-1]

        price_1 = float(
            df["High"].iloc[first]
        )

        price_2 = float(
            df["High"].iloc[second]
        )

        rsi_1 = float(
            df["RSI_14"].iloc[first]
        )

        rsi_2 = float(
            df["RSI_14"].iloc[second]
        )

        if (
            price_2 > price_1
            and rsi_2 < rsi_1
        ):

            price_change = (
                (price_2 - price_1)
                / price_1
                * 100
            )

            rsi_change = (
                rsi_1 - rsi_2
            )

            score = 50

            if price_change >= 0.5:
                score += 10

            if price_change >= 1.0:
                score += 10

            if rsi_change >= 3:
                score += 10

            if rsi_change >= 5:
                score += 10

            if rsi_1 >= 65:
                score += 10

            bearish_candidate = {
                "divergence": "REGULAR_BEARISH",
                "direction": "BEARISH",
                "confidence": min(
                    score,
                    100,
                ),
                "price_point_1": price_1,
                "price_point_2": price_2,
                "rsi_point_1": rsi_1,
                "rsi_point_2": rsi_2,
                "time_point_1": df.index[first],
                "time_point_2": df.index[second],
                "reasons": [
                    "Price formed a higher swing high",
                    "RSI formed a lower swing high",
                ],
            }

    # --------------------------------------------------
    # CHOOSE MOST RECENT DIVERGENCE
    # --------------------------------------------------

    candidates = [
        candidate
        for candidate in (
            bullish_candidate,
            bearish_candidate,
        )
        if candidate is not None
    ]

    if not candidates:

        result["reasons"].append(
            "No regular RSI divergence detected"
        )
        return result

    result = max(
        candidates,
        key=lambda x: x["time_point_2"],
    )

    return result