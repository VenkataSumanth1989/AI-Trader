import pandas as pd
import numpy as np


def detect_support_resistance(
    data: pd.DataFrame,
    lookback: int = 120,
    swing_window: int = 3,
    tolerance_percent: float = 0.30,
) -> dict:
    """
    Detect recent support/resistance levels from confirmed swing lows/highs
    and determine whether price is testing or breaking those levels.
    """

    result = {
        "support": None,
        "resistance": None,
        "support_touches": 0,
        "resistance_touches": 0,
        "price": None,
        "support_distance_percent": None,
        "resistance_distance_percent": None,
        "breakout": "NONE",
        "breakout_level": None,
        "breakout_distance_percent": None,
        "position": "UNKNOWN",
        "confidence": 0,
        "reasons": [],
        "warnings": [],
    }

    required = {"High", "Low", "Close"}

    if not required.issubset(data.columns):
        result["warnings"].append("Required High/Low/Close columns are missing.")
        return result

    df = data[["High", "Low", "Close"]].dropna().copy()

    min_needed = max(20, (swing_window * 2) + 5)

    if len(df) < min_needed:
        result["warnings"].append(
            "Not enough candles for support/resistance analysis."
        )
        return result

    df = df.tail(lookback).copy()

    swing_highs = []
    swing_lows = []

    for i in range(swing_window, len(df) - swing_window):
        local_highs = df["High"].iloc[
            i - swing_window:
            i + swing_window + 1
        ]

        local_lows = df["Low"].iloc[
            i - swing_window:
            i + swing_window + 1
        ]

        current_high = float(df["High"].iloc[i])
        current_low = float(df["Low"].iloc[i])

        if current_high == float(local_highs.max()):
            swing_highs.append({
                "price": current_high,
                "time": df.index[i],
            })

        if current_low == float(local_lows.min()):
            swing_lows.append({
                "price": current_low,
                "time": df.index[i],
            })

    current_price = float(df["Close"].iloc[-1])
    result["price"] = current_price

    if not swing_highs or not swing_lows:
        result["warnings"].append(
            "Not enough confirmed swing highs/lows were found."
        )
        return result

    def cluster_levels(points):
        clusters = []

        for point in points:
            price = float(point["price"])
            placed = False

            for cluster in clusters:
                center = cluster["center"]

                if center == 0:
                    continue

                distance_percent = abs(price - center) / center * 100

                if distance_percent <= tolerance_percent:
                    cluster["prices"].append(price)
                    cluster["times"].append(point["time"])
                    cluster["center"] = float(np.mean(cluster["prices"]))
                    placed = True
                    break

            if not placed:
                clusters.append({
                    "center": price,
                    "prices": [price],
                    "times": [point["time"]],
                })

        for cluster in clusters:
            cluster["touches"] = len(cluster["prices"])
            cluster["latest_time"] = max(cluster["times"])

        return clusters

    support_clusters = cluster_levels(swing_lows)
    resistance_clusters = cluster_levels(swing_highs)

    supports_below = [
        c for c in support_clusters
        if c["center"] <= current_price
    ]

    resistances_above = [
        c for c in resistance_clusters
        if c["center"] >= current_price
    ]

    if supports_below:
        support_cluster = max(
            supports_below,
            key=lambda c: (
                c["touches"],
                c["latest_time"],
                c["center"],
            ),
        )
    else:
        support_cluster = min(
            support_clusters,
            key=lambda c: abs(c["center"] - current_price),
        )

    if resistances_above:
        resistance_cluster = max(
            resistances_above,
            key=lambda c: (
                c["touches"],
                c["latest_time"],
                -c["center"],
            ),
        )
    else:
        resistance_cluster = min(
            resistance_clusters,
            key=lambda c: abs(c["center"] - current_price),
        )

    support = float(support_cluster["center"])
    resistance = float(resistance_cluster["center"])

    support_touches = int(support_cluster["touches"])
    resistance_touches = int(resistance_cluster["touches"])

    result["support"] = support
    result["resistance"] = resistance
    result["support_touches"] = support_touches
    result["resistance_touches"] = resistance_touches

    if current_price:
        result["support_distance_percent"] = (
            (current_price - support) / current_price * 100
        )
        result["resistance_distance_percent"] = (
            (resistance - current_price) / current_price * 100
        )

    breakout = "NONE"
    breakout_level = None
    breakout_distance_percent = None

    if current_price > resistance:
        breakout = "BULLISH_BREAKOUT"
        breakout_level = resistance
        breakout_distance_percent = (
            (current_price - resistance) / resistance * 100
        )

    elif current_price < support:
        breakout = "BEARISH_BREAKDOWN"
        breakout_level = support
        breakout_distance_percent = (
            (support - current_price) / support * 100
        )

    result["breakout"] = breakout
    result["breakout_level"] = breakout_level
    result["breakout_distance_percent"] = breakout_distance_percent

    if support <= current_price <= resistance:
        result["position"] = "INSIDE_RANGE"
    elif current_price > resistance:
        result["position"] = "ABOVE_RESISTANCE"
    else:
        result["position"] = "BELOW_SUPPORT"

    confidence = 50
    confidence += min(support_touches * 5, 15)
    confidence += min(resistance_touches * 5, 15)

    if breakout != "NONE":
        confidence += 10
        if (
            breakout_distance_percent is not None
            and breakout_distance_percent >= 0.50
        ):
            confidence += 10

    result["confidence"] = min(int(confidence), 100)

    result["reasons"].append(
        f"Support identified near ${support:.2f} "
        f"from {support_touches} confirmed swing touch(es)."
    )
    result["reasons"].append(
        f"Resistance identified near ${resistance:.2f} "
        f"from {resistance_touches} confirmed swing touch(es)."
    )

    if breakout == "BULLISH_BREAKOUT":
        result["reasons"].append(
            f"Price closed above resistance near ${resistance:.2f}."
        )
    elif breakout == "BEARISH_BREAKDOWN":
        result["reasons"].append(
            f"Price closed below support near ${support:.2f}."
        )
    else:
        result["reasons"].append(
            "Price is currently trading between detected support and resistance."
        )

    return result