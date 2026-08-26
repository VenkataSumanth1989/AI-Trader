import pandas as pd
import numpy as np


def add_obv(
    data: pd.DataFrame,
    signal_period: int = 20,
) -> pd.DataFrame:
    """Add OBV, its moving average, and recent change."""
    result = data.copy()

    price_diff = result["Close"].diff()

    direction = pd.Series(
        np.sign(price_diff),
        index=result.index,
        dtype="float64",
    ).fillna(0.0)

    result["OBV"] = (
        direction * result["Volume"].fillna(0.0)
    ).cumsum()

    result["OBV_SIGNAL"] = (
        result["OBV"]
        .rolling(window=signal_period)
        .mean()
    )

    result["OBV_CHANGE"] = (
        result["OBV"]
        .diff(signal_period)
    )

    return result


def analyze_obv(row: pd.Series) -> dict:
    """Interpret the latest OBV reading as supporting evidence."""
    required = ["OBV", "OBV_SIGNAL", "OBV_CHANGE"]

    for column in required:
        if column not in row.index:
            return {
                "signal": "UNKNOWN",
                "direction": "NEUTRAL",
                "confidence": 0,
                "reasons": ["OBV data unavailable"],
                "warnings": [],
            }

        if pd.isna(row[column]):
            return {
                "signal": "UNKNOWN",
                "direction": "NEUTRAL",
                "confidence": 0,
                "reasons": ["OBV values not ready"],
                "warnings": [],
            }

    obv = float(row["OBV"])
    obv_signal = float(row["OBV_SIGNAL"])
    obv_change = float(row["OBV_CHANGE"])

    reasons = []
    warnings = []

    if obv > obv_signal and obv_change > 0:
        signal = "BULLISH_VOLUME_CONFIRMATION"
        direction = "BULLISH"
        confidence = 70
        reasons.extend(
            [
                "OBV is above its moving average",
                "OBV has increased over the recent period",
            ]
        )

    elif obv < obv_signal and obv_change < 0:
        signal = "BEARISH_VOLUME_CONFIRMATION"
        direction = "BEARISH"
        confidence = 70
        reasons.extend(
            [
                "OBV is below its moving average",
                "OBV has decreased over the recent period",
            ]
        )

    else:
        signal = "MIXED_VOLUME"
        direction = "NEUTRAL"
        confidence = 45
        reasons.append(
            "OBV direction and OBV moving average are not providing "
            "the same confirmation"
        )

    return {
        "signal": signal,
        "direction": direction,
        "confidence": confidence,
        "obv": obv,
        "obv_signal": obv_signal,
        "obv_change": obv_change,
        "reasons": reasons,
        "warnings": warnings,
    }
