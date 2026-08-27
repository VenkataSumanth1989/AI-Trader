import pandas as pd


def confirm_entry(row: pd.Series, pullback: dict) -> dict:
    """
    Confirm whether price action is ready for a potential entry.

    This function does NOT place trades.
    It evaluates confirmation after a pullback or trend setup.
    """

    setup_type = pullback.get("type", "NO_CLEAR_PULLBACK")

    bullish = 0
    bearish = 0

    reasons = []
    warnings = []

    close = row["Close"]

    # --------------------------------------------------
    # BULLISH PULLBACK
    # --------------------------------------------------

    if setup_type == "HEALTHY_BULLISH_PULLBACK":

        # Price reclaiming VWAP
        if close > row["VWAP"]:
            bullish += 2
            reasons.append("Price above VWAP")

        else:
            warnings.append("Price remains below VWAP")

        # EMA structure
        if row["EMA_9"] > row["EMA_20"]:
            bullish += 2
            reasons.append("EMA 9 reclaimed EMA 20")

        else:
            warnings.append("EMA 9 remains below EMA 20")

        # RSI recovery
        if row["RSI_14"] >= 50:
            bullish += 1
            reasons.append("RSI supports bullish momentum")

        else:
            warnings.append("RSI remains below 50")

        # MACD
        if row["MACD"] > row["MACD_SIGNAL"]:
            bullish += 2
            reasons.append("MACD bullish confirmation")

        else:
            warnings.append("MACD has not confirmed bullish reversal")

        # MACD histogram
        if row["MACD_HISTOGRAM"] > 0:
            bullish += 1
            reasons.append("MACD histogram positive")

        # DI
        if row["DI_PLUS_14"] > row["DI_MINUS_14"]:
            bullish += 1
            reasons.append("DI+ above DI-")

        else:
            warnings.append("DI- remains above DI+")

        # Volume
        if row["RELATIVE_VOLUME"] >= 1.5:
            bullish += 1
            reasons.append("Volume confirms move")

        else:
            warnings.append("Volume confirmation is weak")

        # --------------------------------------------------
        # DECISION
        # --------------------------------------------------

        if bullish >= 7:

            return {
                "confirmed": True,
                "direction": "LONG",
                "confidence": min(95, 60 + bullish * 5),
                "bullish_evidence": bullish,
                "bearish_evidence": bearish,
                "max_evidence": 10,
                "decision": "ENTRY_CONFIRMED",
                "reasons": reasons,
                "warnings": warnings,
            }

        if bullish >= 4:

            return {
                "confirmed": False,
                "direction": "LONG",
                "confidence": 50 + bullish * 4,
                "bullish_evidence": bullish,
                "bearish_evidence": bearish,
                "max_evidence": 10,
                "decision": "WAIT_FOR_CONFIRMATION",
                "reasons": reasons,
                "warnings": warnings,
            }

        return {
            "confirmed": False,
            "direction": "LONG",
            "confidence": 40,
            "bullish_evidence": bullish,
            "bearish_evidence": bearish,
            "decision": "NO_ENTRY",
            "reasons": reasons,
            "warnings": warnings,
        }

    # --------------------------------------------------
    # BEARISH PULLBACK
    # --------------------------------------------------

    if setup_type == "HEALTHY_BEARISH_PULLBACK":

        # Price below VWAP
        if close < row["VWAP"]:
            bearish += 2
            reasons.append("Price below VWAP")

        else:
            warnings.append("Price remains above VWAP")

        # EMA structure
        if row["EMA_9"] < row["EMA_20"]:
            bearish += 2
            reasons.append("EMA 9 below EMA 20")

        else:
            warnings.append("EMA 9 remains above EMA 20")

        # RSI
        if row["RSI_14"] <= 50:
            bearish += 1
            reasons.append("RSI supports bearish momentum")

        else:
            warnings.append("RSI remains above 50")

        # MACD
        if row["MACD"] < row["MACD_SIGNAL"]:
            bearish += 2
            reasons.append("MACD bearish confirmation")

        else:
            warnings.append("MACD has not confirmed bearish reversal")

        # Histogram
        if row["MACD_HISTOGRAM"] < 0:
            bearish += 1
            reasons.append("MACD histogram negative")

        # DI
        if row["DI_MINUS_14"] > row["DI_PLUS_14"]:
            bearish += 1
            reasons.append("DI- above DI+")

        else:
            warnings.append("DI+ remains above DI-")

        # Volume
        if row["RELATIVE_VOLUME"] >= 1.5:
            bearish += 1
            reasons.append("Volume confirms move")

        else:
            warnings.append("Volume confirmation is weak")

        # --------------------------------------------------
        # DECISION
        # --------------------------------------------------

        if bearish >= 7:

            return {
                "confirmed": True,
                "direction": "SHORT",
                "confidence": min(95, 60 + bearish * 5),
                "bullish_evidence": bullish,
                "bearish_evidence": bearish,
                "max_evidence": 10,
                "decision": "ENTRY_CONFIRMED",
                "reasons": reasons,
                "warnings": warnings,
            }

        if bearish >= 4:

            return {
                "confirmed": False,
                "direction": "SHORT",
                "confidence": 50 + bearish * 4,
                "bullish_evidence": bullish,
                "bearish_evidence": bearish,
                "max_evidence": 10,
                "decision": "WAIT_FOR_CONFIRMATION",
                "reasons": reasons,
                "warnings": warnings,
            }

        return {
            "confirmed": False,
            "direction": "SHORT",
            "confidence": 40,
            "bullish_evidence": bullish,
            "bearish_evidence": bearish,
            "decision": "NO_ENTRY",
            "reasons": reasons,
            "warnings": warnings,
        }

    # --------------------------------------------------
    # TREND CONTINUATION
    # --------------------------------------------------

    if setup_type == "TREND_CONTINUATION":

        bullish_conditions = (
            close > row["VWAP"]
            and row["EMA_9"] > row["EMA_20"]
            and row["EMA_20"] > row["EMA_50"]
            and row["MACD"] > row["MACD_SIGNAL"]
            and row["DI_PLUS_14"] > row["DI_MINUS_14"]
        )

        bearish_conditions = (
            close < row["VWAP"]
            and row["EMA_9"] < row["EMA_20"]
            and row["EMA_20"] < row["EMA_50"]
            and row["MACD"] < row["MACD_SIGNAL"]
            and row["DI_MINUS_14"] > row["DI_PLUS_14"]
        )

        if bullish_conditions:

            return {
                "confirmed": True,
                "direction": "LONG",
                "confidence": 85,
                "bullish_evidence": 5,
                "bearish_evidence": 0,
                "max_evidence": 5,
                "decision": "ENTRY_CONFIRMED",
                "reasons": [
                    "Trend continuation conditions aligned"
                ],
                "warnings": [],
            }

        if bearish_conditions:

            return {
                "confirmed": True,
                "direction": "SHORT",
                "confidence": 85,
                "bullish_evidence": 0,
                "bearish_evidence": 5,
                "max_evidence": 5,
                "decision": "ENTRY_CONFIRMED",
                "reasons": [
                    "Bearish continuation conditions aligned"
                ],
                "warnings": [],
            }

    # --------------------------------------------------
    # REVERSAL RISK / NO SETUP
    # --------------------------------------------------

    return {
        "confirmed": False,
        "direction": "NONE",
        "confidence": 0,
        "bullish_evidence": 0,
        "bearish_evidence": 0,
        "max_evidence": 0,
        "decision": "NO_ENTRY",
        "reasons": [],
        "warnings": [
            "No valid entry setup requiring confirmation"
        ],
    }