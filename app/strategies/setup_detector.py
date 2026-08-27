import pandas as pd


def detect_setup(row: pd.Series) -> dict:
    """
    Detect the current market setup.

    This function does NOT place trades.

    It evaluates:
        - Intraday direction
        - Long-term market regime
        - Trend continuation
        - Pullback conditions
        - Breakout potential
        - Counter-trend conditions
        - Risk warnings

    The detector identifies opportunities.
    It does not guarantee future price movement.
    """

    bullish = 0
    bearish = 0

    reasons = []
    warnings = []

    # --------------------------------------------------
    # BASIC VALUES
    # --------------------------------------------------

    close = row["Close"]
    vwap = row["VWAP"]

    ema_9 = row["EMA_9"]
    ema_20 = row["EMA_20"]
    ema_50 = row["EMA_50"]

    rsi = row["RSI_14"]

    macd = row["MACD"]
    macd_signal = row["MACD_SIGNAL"]
    macd_histogram = row["MACD_HISTOGRAM"]

    stoch_k = row["STOCH_K"]
    stoch_d = row["STOCH_D"]

    adx = row["ADX_14"]
    di_plus = row["DI_PLUS_14"]
    di_minus = row["DI_MINUS_14"]

    relative_volume = row["RELATIVE_VOLUME"]
    atr = row["ATR_14"]

    # --------------------------------------------------
    # LONG-TERM MARKET REGIME
    # --------------------------------------------------

    market_regime = "UNKNOWN"

    if (
        "SMA_50" in row.index
        and "SMA_200" in row.index
        and not pd.isna(row["SMA_50"])
        and not pd.isna(row["SMA_200"])
    ):

        sma_50 = row["SMA_50"]
        sma_200 = row["SMA_200"]

        if close > sma_200 and sma_50 > sma_200:
            market_regime = "BULLISH"

        elif close < sma_200 and sma_50 < sma_200:
            market_regime = "BEARISH"

        else:
            market_regime = "NEUTRAL"

    # --------------------------------------------------
    # PRICE / VWAP
    # --------------------------------------------------

    price_above_vwap = close > vwap

    if price_above_vwap:
        bullish += 1
        reasons.append("Price above VWAP")
    else:
        bearish += 1
        reasons.append("Price below VWAP")

    # --------------------------------------------------
    # EMA STRUCTURE
    # --------------------------------------------------

    ema_bullish = (
        ema_9 > ema_20
        and ema_20 > ema_50
    )

    ema_bearish = (
        ema_9 < ema_20
        and ema_20 < ema_50
    )

    if ema_bullish:
        bullish += 2
        reasons.append("EMA structure bullish")

    elif ema_bearish:
        bearish += 2
        reasons.append("EMA structure bearish")

    # --------------------------------------------------
    # RSI
    # --------------------------------------------------

    if rsi >= 50:
        bullish += 1
        reasons.append("RSI supports bullish momentum")
    else:
        bearish += 1
        reasons.append("RSI below bullish threshold")

    if rsi >= 70:
        warnings.append("RSI overbought")

    elif rsi <= 30:
        warnings.append("RSI oversold")

    # --------------------------------------------------
    # MACD
    # --------------------------------------------------

    macd_bullish = macd > macd_signal

    if macd_bullish:
        bullish += 1
        reasons.append("MACD bullish")
    else:
        bearish += 1
        reasons.append("MACD bearish")

    if macd_histogram > 0:
        bullish += 1
        reasons.append("MACD histogram positive")
    else:
        bearish += 1
        reasons.append("MACD histogram negative")

    # --------------------------------------------------
    # STOCHASTIC
    # --------------------------------------------------

    stoch_bullish = stoch_k > stoch_d

    if stoch_bullish:
        bullish += 1
        reasons.append("Stochastic %K above %D")
    else:
        bearish += 1
        reasons.append("Stochastic %K below %D")

    if stoch_k >= 80:
        warnings.append("Stochastic overbought")

    elif stoch_k <= 20:
        warnings.append("Stochastic oversold")

    # --------------------------------------------------
    # ADX + DIRECTIONAL INDICATORS
    # --------------------------------------------------

    di_bullish = di_plus > di_minus
    di_bearish = di_minus > di_plus

    if di_bullish:
        bullish += 1
        reasons.append("DI+ above DI-")

    elif di_bearish:
        bearish += 1
        reasons.append("DI- above DI+")

    if adx >= 25:
        reasons.append("ADX confirms meaningful trend")
    else:
        warnings.append("ADX indicates weak/developing trend")

    # --------------------------------------------------
    # RELATIVE VOLUME
    # --------------------------------------------------

    strong_volume = relative_volume >= 1.5

    if strong_volume:
        bullish += 1
        reasons.append("Volume confirms the move")
    else:
        warnings.append("Volume confirmation is weak")

    # --------------------------------------------------
    # MARKET REGIME EVIDENCE
    # --------------------------------------------------

    if market_regime == "BULLISH":
        bullish += 2
        reasons.append("Long-term market regime bullish")

    elif market_regime == "BEARISH":
        bearish += 2
        reasons.append("Long-term market regime bearish")

    # --------------------------------------------------
    # DIRECTION
    # --------------------------------------------------

    total_evidence = bullish + bearish

    if total_evidence == 0:
        bullish_ratio = 0.5
    else:
        bullish_ratio = bullish / total_evidence

    if bullish_ratio >= 0.65:
        direction = "BULLISH"

    elif bullish_ratio <= 0.35:
        direction = "BEARISH"

    else:
        direction = "NEUTRAL"

    # --------------------------------------------------
    # SETUP DETECTION
    # --------------------------------------------------

    setup = "NO_SETUP"

    # ==================================================
    # BULLISH TREND CONTINUATION
    # ==================================================

    if (
        market_regime == "BULLISH"
        and direction == "BULLISH"
        and ema_bullish
        and price_above_vwap
        and macd_bullish
        and di_bullish
        and adx >= 25
        and strong_volume
    ):
        setup = "TREND_CONTINUATION"

    # ==================================================
    # BULLISH PULLBACK
    #
    # We identify a developing pullback-style condition
    # rather than claiming a confirmed pullback.
    # ==================================================

    elif (
        market_regime == "BULLISH"
        and direction == "BULLISH"
        and ema_20 >= ema_50
        and (
            close <= ema_20 * 1.01
            or close <= vwap * 1.01
        )
        and rsi >= 45
        and macd_histogram >= 0
    ):
        setup = "BULLISH_PULLBACK"

    # ==================================================
    # BULLISH EARLY TREND
    # ==================================================

    elif (
        market_regime == "BULLISH"
        and direction == "BULLISH"
        and ema_bullish
        and price_above_vwap
        and macd_bullish
        and adx < 25
    ):
        setup = "EARLY_BULLISH_TREND"

    # ==================================================
    # BEARISH TREND CONTINUATION
    # ==================================================

    elif (
        market_regime == "BEARISH"
        and direction == "BEARISH"
        and ema_bearish
        and not price_above_vwap
        and not macd_bullish
        and di_bearish
        and adx >= 25
        and strong_volume
    ):
        setup = "BEARISH_CONTINUATION"

    # ==================================================
    # BEARISH PULLBACK
    # ==================================================

    elif (
        market_regime == "BEARISH"
        and direction == "BEARISH"
        and ema_20 <= ema_50
        and (
            close >= ema_20 * 0.99
            or close >= vwap * 0.99
        )
        and rsi <= 55
        and macd_histogram <= 0
    ):
        setup = "BEARISH_PULLBACK"

    # ==================================================
    # COUNTER-TREND BULLISH BOUNCE
    # ==================================================

    elif (
        market_regime == "BEARISH"
        and direction == "BULLISH"
        and macd_bullish
        and rsi > 50
    ):
        setup = "COUNTER_TREND_BOUNCE"

        warnings.append(
            "Bullish setup is against the long-term trend"
        )

    # ==================================================
    # COUNTER-TREND BEARISH BOUNCE
    # ==================================================

    elif (
        market_regime == "BULLISH"
        and direction == "BEARISH"
        and not macd_bullish
        and rsi < 50
    ):
        setup = "COUNTER_TREND_BEARISH"

        warnings.append(
            "Bearish setup is against the long-term trend"
        )

    # --------------------------------------------------
    # EXTENSION / RISK
    # --------------------------------------------------

    if atr > 0:

        distance_from_vwap = abs(close - vwap)

        extension = (
            distance_from_vwap / atr
        )

        if extension >= 2:
            warnings.append(
                "Price extended more than 2 ATR from VWAP"
            )

    # --------------------------------------------------
    # ADDITIONAL RISK WARNINGS
    # --------------------------------------------------

    if rsi >= 70:
        warnings.append(
            "Momentum may be extended"
        )

    if stoch_k >= 80 and stoch_k < stoch_d:
        warnings.append(
            "Stochastic showing potential momentum rollover"
        )

    if relative_volume < 0.75:
        warnings.append(
            "Very low volume may reduce signal reliability"
        )

    # --------------------------------------------------
    # CONFIDENCE
    # --------------------------------------------------

    if total_evidence == 0:

        confidence = 50

    else:

        confidence = int(
            round(
                max(
                    bullish_ratio,
                    1 - bullish_ratio
                ) * 100
            )
        )

    # Reduce confidence for weak conditions

    if relative_volume < 1.0:
        confidence -= 8

    if adx < 20:
        confidence -= 8

    elif adx < 25:
        confidence -= 4

    # Counter-trend setups should have lower confidence

    if setup in (
        "COUNTER_TREND_BOUNCE",
        "COUNTER_TREND_BEARISH",
    ):
        confidence -= 10

    # No setup should never look like a high-quality entry

    if setup == "NO_SETUP":
        confidence = min(confidence, 60)

    confidence = max(
        0,
        min(100, confidence)
    )

    # --------------------------------------------------
    # SETUP QUALITY
    # --------------------------------------------------

    if setup == "TREND_CONTINUATION":
        quality = "HIGH"

    elif setup in (
        "BULLISH_PULLBACK",
        "BEARISH_PULLBACK",
        "EARLY_BULLISH_TREND",
    ):
        quality = "MEDIUM"

    elif setup in (
        "COUNTER_TREND_BOUNCE",
        "COUNTER_TREND_BEARISH",
    ):
        quality = "LOW"

    else:
        quality = "NONE"

    # --------------------------------------------------
    # RETURN RESULT
    # --------------------------------------------------

    return {
        "setup": setup,
        "direction": direction,
        "market_regime": market_regime,
        "confidence": confidence,
        "quality": quality,
        "bullish_evidence": bullish,
        "bearish_evidence": bearish,
        "total_evidence": total_evidence,
        "bullish_ratio": round(bullish_ratio * 100, 1),
        "bearish_ratio": round((1 - bullish_ratio) * 100, 1),
        "confidence_adjustments": {
            "low_volume": -8 if relative_volume < 1.0 else 0,
            "weak_adx": -8 if adx < 20 else (-4 if adx < 25 else 0),
            "counter_trend": -10 if setup in (
                "COUNTER_TREND_BOUNCE",
                "COUNTER_TREND_BEARISH",
            ) else 0,
            "no_setup_cap": 60 if setup == "NO_SETUP" else None,
        },
        "reasons": reasons,
        "warnings": warnings,
    }