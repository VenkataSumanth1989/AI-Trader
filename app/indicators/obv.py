import pandas as pd
import numpy as np


def add_obv(
    data: pd.DataFrame,
    signal_period: int = 20,
) -> pd.DataFrame:
    """
    Add On-Balance Volume (OBV) indicators.

    OBV rises when price closes higher and falls when
    price closes lower.

    Also calculates:
        OBV_SIGNAL  - moving average of OBV
        OBV_CHANGE  - recent OBV change
    """

    result = data.copy()

    price_change = result["Close"].diff()

    direction = np.where(
        price_change > 0,
        1,
        np.where(
            price_change < 0,
            -1,
            0,
        ),
    )

    result["OBV"] = (
        pd.Series(
            direction,
            index=result.index,
        )
        * result["Volume"]
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


def analyze_obv(
    row: pd.Series,
) -> dict:
    """
    Interpret the latest OBV reading.

    OBV is used as supporting volume evidence and
    does not create a trade by itself.
    """

    required = [
        "OBV",
        "OBV_SIGNAL",
        "OBV_CHANGE",
    ]

    for column in required:

        if column not in row.index:

            return {
                "signal": "UNKNOWN",
                "direction": "NEUTRAL",
                "confidence": 0,
                "reasons": [
                    "OBV data unavailable"
                ],
                "warnings": [],
            }

        if pd.isna(row[column]):

            return {
                "signal": "UNKNOWN",
                "direction": "NEUTRAL",
                "confidence": 0,
                "reasons": [
                    "OBV values not ready"
                ],
                "warnings": [],
            }

    obv = float(row["OBV"])
    obv_signal = float(row["OBV_SIGNAL"])
    obv_change = float(row["OBV_CHANGE"])

    reasons = []
    warnings = []

    # --------------------------------------------------
    # BULLISH OBV
    # --------------------------------------------------

    if (
        obv > obv_signal
        and obv_change > 0
    ):

        signal = "BULLISH_VOLUME_CONFIRMATION"
        direction = "BULLISH"
        confidence = 70

        reasons.append(
            "OBV is above its moving average"
        )

        reasons.append(
            "OBV has increased over the recent period"
        )

    # --------------------------------------------------
    # BEARISH OBV
    # --------------------------------------------------

    elif (
        obv < obv_signal
        and obv_change < 0
    ):

        signal = "BEARISH_VOLUME_CONFIRMATION"
        direction = "BEARISH"
        confidence = 70

        reasons.append(
            "OBV is below its moving average"
        )

        reasons.append(
            "OBV has decreased over the recent period"
        )

    # --------------------------------------------------
    # MIXED
    # --------------------------------------------------

    else:

        signal = "MIXED_VOLUME"
        direction = "NEUTRAL"
        confidence = 45

        reasons.append(
            "OBV direction and OBV moving average "
            "are not providing the same confirmation"
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