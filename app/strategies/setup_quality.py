import pandas as pd


def calculate_setup_quality(row: pd.Series, setup: dict) -> dict:
    """
    Evaluate the quality of a detected trading setup.

    This does NOT place trades.
    It evaluates trend, momentum, volume, volatility,
    and risk characteristics.
    """

    score = 0
    reasons = []
    warnings = []

    # --------------------------------------------------
    # 1. LONG-TERM TREND
    # --------------------------------------------------

    market_regime = setup.get("market_regime", "UNKNOWN")
    direction = setup.get("direction", "NEUTRAL")

    if direction == "BULLISH" and market_regime == "BULLISH":
        score += 20
        reasons.append("Direction aligned with bullish long-term trend")

    elif direction == "BEARISH" and market_regime == "BEARISH":
        score += 20
        reasons.append("Direction aligned with bearish long-term trend")

    elif market_regime == "UNKNOWN":
        warnings.append("Long-term trend unavailable")

    else:
        warnings.append("Direction conflicts with long-term trend")

    # --------------------------------------------------
    # 2. EMA STRUCTURE
    # --------------------------------------------------

    ema_bullish = (
        row["EMA_9"] > row["EMA_20"]
        and row["EMA_20"] > row["EMA_50"]
    )

    ema_bearish = (
        row["EMA_9"] < row["EMA_20"]
        and row["EMA_20"] < row["EMA_50"]
    )

    if direction == "BULLISH" and ema_bullish:
        score += 15
        reasons.append("EMA structure supports bullish direction")

    elif direction == "BEARISH" and ema_bearish:
        score += 15
        reasons.append("EMA structure supports bearish direction")

    else:
        warnings.append("EMA structure is not fully aligned")

    # --------------------------------------------------
    # 3. VWAP
    # --------------------------------------------------

    if direction == "BULLISH" and row["Close"] > row["VWAP"]:
        score += 15
        reasons.append("Price above VWAP")

    elif direction == "BEARISH" and row["Close"] < row["VWAP"]:
        score += 15
        reasons.append("Price below VWAP")

    else:
        warnings.append("Price is on the wrong side of VWAP")

    # --------------------------------------------------
    # 4. MACD MOMENTUM
    # --------------------------------------------------

    macd_bullish = (
        row["MACD"] > row["MACD_SIGNAL"]
        and row["MACD_HISTOGRAM"] > 0
    )

    macd_bearish = (
        row["MACD"] < row["MACD_SIGNAL"]
        and row["MACD_HISTOGRAM"] < 0
    )

    if direction == "BULLISH" and macd_bullish:
        score += 15
        reasons.append("MACD confirms bullish momentum")

    elif direction == "BEARISH" and macd_bearish:
        score += 15
        reasons.append("MACD confirms bearish momentum")

    else:
        warnings.append("MACD momentum is not fully confirmed")

    # --------------------------------------------------
    # 5. ADX + DI
    # --------------------------------------------------

    adx = row["ADX_14"]
    di_plus = row["DI_PLUS_14"]
    di_minus = row["DI_MINUS_14"]

    if direction == "BULLISH" and di_plus > di_minus:
        score += 10
        reasons.append("Directional movement supports buyers")

    elif direction == "BEARISH" and di_minus > di_plus:
        score += 10
        reasons.append("Directional movement supports sellers")

    else:
        warnings.append("Directional movement is not aligned")

    if adx >= 25:
        score += 5
        reasons.append("ADX confirms meaningful trend")
    else:
        warnings.append("ADX indicates weak/developing trend")

    # --------------------------------------------------
    # 6. RELATIVE VOLUME
    # --------------------------------------------------

    relative_volume = row["RELATIVE_VOLUME"]

    if relative_volume >= 1.5:
        score += 10
        reasons.append("Volume confirms participation")

    elif relative_volume < 1.0:
        warnings.append("Below-average volume")

    else:
        warnings.append("Volume confirmation is moderate")

    # --------------------------------------------------
    # 7. RSI
    # --------------------------------------------------

    rsi = row["RSI_14"]

    if direction == "BULLISH":

        if 50 <= rsi < 70:
            score += 5
            reasons.append("RSI in healthy bullish zone")

        elif rsi >= 70:
            warnings.append("RSI is overbought")

        else:
            warnings.append("RSI does not confirm bullish momentum")

    elif direction == "BEARISH":

        if 30 < rsi <= 50:
            score += 5
            reasons.append("RSI supports bearish momentum")

        elif rsi <= 30:
            warnings.append("RSI is oversold")

        else:
            warnings.append("RSI does not confirm bearish momentum")

    # --------------------------------------------------
    # 8. STOCHASTIC
    # --------------------------------------------------

    stoch_k = row["STOCH_K"]
    stoch_d = row["STOCH_D"]

    if direction == "BULLISH":

        if stoch_k > stoch_d and stoch_k < 80:
            score += 5
            reasons.append("Stochastic supports bullish momentum")

        elif stoch_k >= 80:
            warnings.append("Stochastic is overbought")

    elif direction == "BEARISH":

        if stoch_k < stoch_d and stoch_k > 20:
            score += 5
            reasons.append("Stochastic supports bearish momentum")

        elif stoch_k <= 20:
            warnings.append("Stochastic is oversold")

    # --------------------------------------------------
    # 9. PRICE EXTENSION / RISK
    # --------------------------------------------------

    atr = row["ATR_14"]

    if atr > 0:

        distance_from_vwap = abs(
            row["Close"] - row["VWAP"]
        )

        extension = distance_from_vwap / atr

        if extension >= 2:
            warnings.append(
                "Price extended more than 2 ATR from VWAP"
            )
            score -= 10

        elif extension <= 1:
            score += 5
            reasons.append("Price is reasonably close to VWAP")

    # --------------------------------------------------
    # FINAL SCORE
    # --------------------------------------------------

    score = max(0, min(100, score))

    # --------------------------------------------------
    # QUALITY
    # --------------------------------------------------

    if score >= 85:
        quality = "A"
    elif score >= 70:
        quality = "B"
    elif score >= 55:
        quality = "C"
    elif score >= 40:
        quality = "D"
    else:
        quality = "F"

    # --------------------------------------------------
    # ENTRY DECISION
    # --------------------------------------------------

    if quality == "A":
        decision = "HIGH_QUALITY_SETUP"

    elif quality == "B":
        decision = "VALID_SETUP"

    elif quality == "C":
        decision = "WAIT_FOR_CONFIRMATION"

    else:
        decision = "NO_TRADE"

    return {
        "quality": quality,
        "score": score,
        "decision": decision,
        "reasons": reasons,
        "warnings": warnings,
    }