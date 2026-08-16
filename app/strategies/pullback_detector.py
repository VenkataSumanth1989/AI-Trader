import pandas as pd


def detect_pullback(row: pd.Series, setup: dict) -> dict:
    """
    Classify short-term weakness inside a longer-term trend.

    Possible results:

    HEALTHY_BULLISH_PULLBACK
    HEALTHY_BEARISH_PULLBACK
    BEARISH_REVERSAL_RISK
    BULLISH_REVERSAL_RISK
    NO_CLEAR_PULLBACK
    """

    market_regime = setup.get("market_regime", "UNKNOWN")
    direction = setup.get("direction", "NEUTRAL")

    bullish = 0
    bearish = 0

    reasons = []
    warnings = []

    close = row["Close"]
    vwap = row["VWAP"]

    ema9 = row["EMA_9"]
    ema20 = row["EMA_20"]
    ema50 = row["EMA_50"]

    rsi = row["RSI_14"]

    macd = row["MACD"]
    macd_signal = row["MACD_SIGNAL"]
    macd_hist = row["MACD_HISTOGRAM"]

    adx = row["ADX_14"]
    di_plus = row["DI_PLUS_14"]
    di_minus = row["DI_MINUS_14"]

    atr = row["ATR_14"]

    # --------------------------------------------------
    # UNKNOWN TREND
    # --------------------------------------------------

    if market_regime == "UNKNOWN":

        return {
            "pullback": False,
            "type": "NO_CLEAR_PULLBACK",
            "confidence": 0,
            "bullish_evidence": 0,
            "bearish_evidence": 0,
            "reasons": [],
            "warnings": ["Long-term market regime unavailable"],
        }

    # ==================================================
    # BULLISH LONG-TERM REGIME
    # ==================================================

    if market_regime == "BULLISH":

        # --------------------------------------------------
        # LONG-TERM STRUCTURE
        # --------------------------------------------------

        if close > row["SMA_200"]:
            bullish += 2
            reasons.append("Price remains above SMA 200")

        if row["SMA_50"] > row["SMA_200"]:
            bullish += 2
            reasons.append("SMA 50 remains above SMA 200")

        # --------------------------------------------------
        # EMA STRUCTURE
        # --------------------------------------------------

        if ema20 > ema50:
            bullish += 2
            reasons.append("EMA 20 remains above EMA 50")
        else:
            bearish += 2
            warnings.append("EMA 20 has fallen below EMA 50")

        # --------------------------------------------------
        # PRICE LOCATION
        # --------------------------------------------------

        if close > ema50:
            bullish += 1
            reasons.append("Price remains above EMA 50")

        else:
            bearish += 2
            warnings.append("Price has broken below EMA 50")

        # Price near VWAP can indicate a developing pullback
        if close < vwap:

            distance = abs(close - vwap)

            if atr > 0 and distance <= atr:
                bullish += 1
                reasons.append(
                    "Price is pulling back toward VWAP"
                )
            else:
                bearish += 1
                warnings.append(
                    "Price is significantly below VWAP"
                )

        else:
            bullish += 1
            reasons.append("Price remains above VWAP")

        # --------------------------------------------------
        # RSI
        # --------------------------------------------------

        if 40 <= rsi < 55:

            bullish += 2
            reasons.append(
                "RSI has cooled into a potential pullback zone"
            )

        elif 55 <= rsi < 70:

            bullish += 1
            reasons.append(
                "RSI remains in bullish territory"
            )

        elif rsi >= 70:

            warnings.append(
                "RSI is overbought"
            )

        else:

            bearish += 2
            warnings.append(
                "RSI has weakened below 40"
            )

        # --------------------------------------------------
        # MACD
        # --------------------------------------------------

        if macd < macd_signal:

            # MACD weakness is acceptable during a pullback
            bullish += 1
            reasons.append(
                "MACD weakness may represent pullback"
            )

        elif macd_hist > 0:

            bullish += 1
            reasons.append(
                "MACD momentum remains positive"
            )

        # --------------------------------------------------
        # DI / ADX
        # --------------------------------------------------

        if di_plus > di_minus:

            bullish += 2
            reasons.append(
                "DI+ remains above DI-"
            )

        else:

            bearish += 2
            warnings.append(
                "DI- has overtaken DI+"
            )

        if adx >= 25:

            reasons.append(
                "ADX confirms established trend"
            )

        else:

            warnings.append(
                "ADX indicates developing trend"
            )

        # --------------------------------------------------
        # CLASSIFICATION
        # --------------------------------------------------

        if bullish >= 8 and bearish <= 3:

            confidence = min(
                95,
                60 + (bullish - bearish) * 5
            )

            return {
                "pullback": True,
                "type": "HEALTHY_BULLISH_PULLBACK",
                "confidence": confidence,
                "bullish_evidence": bullish,
                "bearish_evidence": bearish,
                "reasons": reasons,
                "warnings": warnings,
            }

        # Possible reversal
        if bearish >= 6:

            confidence = min(
                95,
                55 + (bearish - bullish) * 5
            )

            return {
                "pullback": False,
                "type": "BEARISH_REVERSAL_RISK",
                "confidence": confidence,
                "bullish_evidence": bullish,
                "bearish_evidence": bearish,
                "reasons": reasons,
                "warnings": warnings,
            }

    # ==================================================
    # BEARISH LONG-TERM REGIME
    # ==================================================

    if market_regime == "BEARISH":

        # --------------------------------------------------
        # LONG-TERM STRUCTURE
        # --------------------------------------------------

        if close < row["SMA_200"]:

            bearish += 2
            reasons.append(
                "Price remains below SMA 200"
            )

        if row["SMA_50"] < row["SMA_200"]:

            bearish += 2
            reasons.append(
                "SMA 50 remains below SMA 200"
            )

        # --------------------------------------------------
        # EMA STRUCTURE
        # --------------------------------------------------

        if ema20 < ema50:

            bearish += 2
            reasons.append(
                "EMA 20 remains below EMA 50"
            )

        else:

            bullish += 2
            warnings.append(
                "EMA 20 has moved above EMA 50"
            )

        # --------------------------------------------------
        # PRICE LOCATION
        # --------------------------------------------------

        if close < ema50:

            bearish += 1
            reasons.append(
                "Price remains below EMA 50"
            )

        else:

            bullish += 2
            warnings.append(
                "Price has moved above EMA 50"
            )

        # --------------------------------------------------
        # VWAP
        # --------------------------------------------------

        if close > vwap:

            distance = abs(close - vwap)

            if atr > 0 and distance <= atr:

                bearish += 1
                reasons.append(
                    "Price is pulling back toward VWAP"
                )

            else:

                bullish += 1
                warnings.append(
                    "Price is significantly above VWAP"
                )

        else:

            bearish += 1
            reasons.append(
                "Price remains below VWAP"
            )

        # --------------------------------------------------
        # RSI
        # --------------------------------------------------

        if 45 <= rsi <= 60:

            bearish += 2
            reasons.append(
                "RSI is in a potential bearish pullback zone"
            )

        elif rsi < 45:

            bearish += 1
            reasons.append(
                "RSI supports bearish momentum"
            )

        elif rsi > 60:

            bullish += 2
            warnings.append(
                "RSI is relatively strong"
            )

        # --------------------------------------------------
        # MACD
        # --------------------------------------------------

        if macd > macd_signal:

            bearish += 1
            reasons.append(
                "MACD strength may represent bearish pullback"
            )

        elif macd_hist < 0:

            bearish += 1
            reasons.append(
                "MACD momentum remains negative"
            )

        # --------------------------------------------------
        # DI / ADX
        # --------------------------------------------------

        if di_minus > di_plus:

            bearish += 2
            reasons.append(
                "DI- remains above DI+"
            )

        else:

            bullish += 2
            warnings.append(
                "DI+ has overtaken DI-"
            )

        if adx >= 25:

            reasons.append(
                "ADX confirms established trend"
            )

        else:

            warnings.append(
                "ADX indicates developing trend"
            )

        # --------------------------------------------------
        # CLASSIFICATION
        # --------------------------------------------------

        if bearish >= 8 and bullish <= 3:

            confidence = min(
                95,
                60 + (bearish - bullish) * 5
            )

            return {
                "pullback": True,
                "type": "HEALTHY_BEARISH_PULLBACK",
                "confidence": confidence,
                "bullish_evidence": bullish,
                "bearish_evidence": bearish,
                "reasons": reasons,
                "warnings": warnings,
            }

        if bullish >= 6:

            confidence = min(
                95,
                55 + (bullish - bearish) * 5
            )

            return {
                "pullback": False,
                "type": "BULLISH_REVERSAL_RISK",
                "confidence": confidence,
                "bullish_evidence": bullish,
                "bearish_evidence": bearish,
                "reasons": reasons,
                "warnings": warnings,
            }

    # ==================================================
    # DEFAULT
    # ==================================================

    return {
        "pullback": False,
        "type": "NO_CLEAR_PULLBACK",
        "confidence": 0,
        "bullish_evidence": bullish,
        "bearish_evidence": bearish,
        "reasons": reasons,
        "warnings": warnings,
    }