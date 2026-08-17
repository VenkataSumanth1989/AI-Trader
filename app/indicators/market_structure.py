import pandas as pd


def detect_market_structure_break(
    data: pd.DataFrame,
    swing_window: int = 3,
    lookback: int = 100,
) -> dict:
    """
    Detect recent bullish or bearish Market Structure Break (MSB).

    Bullish MSB:
        Price closes above a prior confirmed swing high.

    Bearish MSB:
        Price closes below a prior confirmed swing low.

    Returns the most recent valid structure break.
    """

    result = {
        "msb": "NONE",
        "direction": "NEUTRAL",
        "break_level": None,
        "break_price": None,
        "break_time": None,
        "swing_time": None,
        "confidence": 0,
        "reasons": [],
    }

    required = {
        "High",
        "Low",
        "Close",
    }

    if not required.issubset(data.columns):
        result["reasons"].append(
            "Required market structure columns are missing"
        )
        return result

    df = data[
        ["High", "Low", "Close"]
    ].dropna().copy()

    if len(df) < 20:
        result["reasons"].append(
            "Not enough candles for market structure analysis"
        )
        return result

    df = df.tail(lookback)

    swing_highs = []
    swing_lows = []

    # --------------------------------------------------
    # FIND CONFIRMED SWINGS
    # --------------------------------------------------

    for i in range(
        swing_window,
        len(df) - swing_window,
    ):

        high_window = df["High"].iloc[
            i - swing_window:
            i + swing_window + 1
        ]

        low_window = df["Low"].iloc[
            i - swing_window:
            i + swing_window + 1
        ]

        current_high = df["High"].iloc[i]
        current_low = df["Low"].iloc[i]

        if current_high == high_window.max():
            swing_highs.append(i)

        if current_low == low_window.min():
            swing_lows.append(i)

    candidates = []

    # --------------------------------------------------
    # BULLISH MSB
    # --------------------------------------------------

    for swing_index in swing_highs:

        swing_level = float(
            df["High"].iloc[swing_index]
        )

        for j in range(
            swing_index + 1,
            len(df),
        ):

            close_price = float(
                df["Close"].iloc[j]
            )

            if close_price > swing_level:

                break_distance = (
                    (close_price - swing_level)
                    / swing_level
                    * 100
                )

                confidence = 60

                if break_distance >= 0.25:
                    confidence += 10

                if break_distance >= 0.50:
                    confidence += 10

                candidates.append({
                    "msb": "BULLISH_MSB",
                    "direction": "BULLISH",
                    "break_level": swing_level,
                    "break_price": close_price,
                    "break_time": df.index[j],
                    "swing_time": df.index[
                        swing_index
                    ],
                    "confidence": min(
                        confidence,
                        100,
                    ),
                    "reasons": [
                        "Price closed above a confirmed swing high",
                        "Bullish market structure break detected",
                    ],
                })

                break

    # --------------------------------------------------
    # BEARISH MSB
    # --------------------------------------------------

    for swing_index in swing_lows:

        swing_level = float(
            df["Low"].iloc[swing_index]
        )

        for j in range(
            swing_index + 1,
            len(df),
        ):

            close_price = float(
                df["Close"].iloc[j]
            )

            if close_price < swing_level:

                break_distance = (
                    (swing_level - close_price)
                    / swing_level
                    * 100
                )

                confidence = 60

                if break_distance >= 0.25:
                    confidence += 10

                if break_distance >= 0.50:
                    confidence += 10

                candidates.append({
                    "msb": "BEARISH_MSB",
                    "direction": "BEARISH",
                    "break_level": swing_level,
                    "break_price": close_price,
                    "break_time": df.index[j],
                    "swing_time": df.index[
                        swing_index
                    ],
                    "confidence": min(
                        confidence,
                        100,
                    ),
                    "reasons": [
                        "Price closed below a confirmed swing low",
                        "Bearish market structure break detected",
                    ],
                })

                break

    # --------------------------------------------------
    # RETURN MOST RECENT BREAK
    # --------------------------------------------------

    if not candidates:
        result["reasons"].append(
            "No confirmed market structure break detected"
        )
        return result

    latest = max(
        candidates,
        key=lambda x: x["break_time"],
    )

    return latest