import math


def _safe_float(value):
    try:
        value = float(value)
        return value if math.isfinite(value) else None
    except (TypeError, ValueError):
        return None


def calculate_intraday_signal(row):
    """
    Calculate a short-term intraday directional signal from the latest
    COMPLETED decision candle.

    Primary weighting:
        EMA 9/20/50   30
        Supertrend    25
        WT_LB         20
        Stochastic    15
        VWAP          10

    Total possible directional score = 100.

    This engine is intentionally independent of the 1-2 day swing bias.
    """

    close = _safe_float(row.get("Close"))

    ema9 = _safe_float(row.get("EMA_9"))
    ema20 = _safe_float(row.get("EMA_20"))
    ema50 = _safe_float(row.get("EMA_50"))

    stoch_k = _safe_float(row.get("STOCH_K"))
    stoch_d = _safe_float(row.get("STOCH_D"))

    wt1 = _safe_float(row.get("WT_LB"))
    wt2 = _safe_float(row.get("WT_LB_SIGNAL"))

    supertrend = _safe_float(row.get("SUPERTREND"))
    supertrend_direction = _safe_float(
        row.get("SUPERTREND_DIRECTION")
    )

    vwap = _safe_float(row.get("VWAP"))

    long_score = 0
    short_score = 0

    bullish_reasons = []
    bearish_reasons = []
    warnings = []

    indicator_states = {}

    # ========================================================
    # EMA — 30 POINTS
    # ========================================================

    if None not in (ema9, ema20, ema50):

        if ema9 > ema20 > ema50:
            long_score += 30
            ema_state = "BULLISH"
            bullish_reasons.append(
                "EMA 9 > EMA 20 > EMA 50"
            )

        elif ema9 < ema20 < ema50:
            short_score += 30
            ema_state = "BEARISH"
            bearish_reasons.append(
                "EMA 9 < EMA 20 < EMA 50"
            )

        else:
            ema_state = "MIXED"

    else:
        ema_state = "NOT_READY"
        warnings.append("EMA values are incomplete")

    indicator_states["ema"] = ema_state

    # ========================================================
    # SUPERTREND — 25 POINTS
    # ========================================================

    if supertrend_direction == 1:

        long_score += 25
        supertrend_state = "BULLISH"

        bullish_reasons.append(
            "Supertrend is bullish"
        )

    elif supertrend_direction == -1:

        short_score += 25
        supertrend_state = "BEARISH"

        bearish_reasons.append(
            "Supertrend is bearish"
        )

    else:

        supertrend_state = "NOT_READY"
        warnings.append(
            "Supertrend direction is unavailable"
        )

    indicator_states["supertrend"] = supertrend_state

    # ========================================================
    # WAVETREND / WT_LB — 20 POINTS
    # ========================================================

    if wt1 is not None and wt2 is not None:

        if wt1 > wt2:

            long_score += 20
            wt_state = "BULLISH"

            bullish_reasons.append(
                "WT_LB main line is above signal"
            )

        elif wt1 < wt2:

            short_score += 20
            wt_state = "BEARISH"

            bearish_reasons.append(
                "WT_LB main line is below signal"
            )

        else:

            wt_state = "NEUTRAL"

    else:

        wt_state = "NOT_READY"
        warnings.append(
            "WT_LB values are unavailable"
        )

    indicator_states["wt_lb"] = wt_state

    # ========================================================
    # STOCHASTIC — 15 POINTS
    # ========================================================

    if stoch_k is not None and stoch_d is not None:

        if stoch_k > stoch_d:

            long_score += 15
            stochastic_state = "BULLISH"

            bullish_reasons.append(
                "Stochastic %K is above %D"
            )

        elif stoch_k < stoch_d:

            short_score += 15
            stochastic_state = "BEARISH"

            bearish_reasons.append(
                "Stochastic %K is below %D"
            )

        else:

            stochastic_state = "NEUTRAL"

    else:

        stochastic_state = "NOT_READY"
        warnings.append(
            "Stochastic values are unavailable"
        )

    indicator_states["stochastic"] = stochastic_state

    # ========================================================
    # VWAP — 10 POINTS
    # ========================================================

    if close is not None and vwap is not None:

        if close > vwap:

            long_score += 10
            vwap_state = "BULLISH"

            bullish_reasons.append(
                "Price is above VWAP"
            )

        elif close < vwap:

            short_score += 10
            vwap_state = "BEARISH"

            bearish_reasons.append(
                "Price is below VWAP"
            )

        else:

            vwap_state = "NEUTRAL"

    else:

        vwap_state = "NOT_READY"
        warnings.append(
            "Price/VWAP values are unavailable"
        )

    indicator_states["vwap"] = vwap_state

    # ========================================================
    # FINAL DIRECTION
    # ========================================================

    score_spread = abs(long_score - short_score)
    strongest_score = max(long_score, short_score)

    # Require both reasonable evidence and separation between sides.
    if long_score >= 60 and long_score - short_score >= 20:

        direction = "LONG"
        confidence = long_score

    elif short_score >= 60 and short_score - long_score >= 20:

        direction = "SHORT"
        confidence = short_score

    else:

        direction = "WAIT"
        confidence = strongest_score

    # ========================================================
    # SIGNAL STRENGTH
    # ========================================================

    if direction == "WAIT":

        signal = "WAIT"

    elif confidence >= 85:

        signal = "STRONG"

    elif confidence >= 70:

        signal = "CANDIDATE"

    else:

        signal = "EARLY"

    # ========================================================
    # ENTRY READINESS
    # ========================================================

    if direction == "LONG":

        required_alignment = (
            ema_state == "BULLISH"
            and supertrend_state == "BULLISH"
        )

    elif direction == "SHORT":

        required_alignment = (
            ema_state == "BEARISH"
            and supertrend_state == "BEARISH"
        )

    else:

        required_alignment = False

    entry_ready = (
        direction in ("LONG", "SHORT")
        and confidence >= 70
        and score_spread >= 30
        and required_alignment
    )

    if entry_ready:
        action = (
            f"{direction} SETUP — wait for completed-candle "
            "entry confirmation"
        )

    elif direction in ("LONG", "SHORT"):
        action = (
            f"{direction} CANDIDATE — additional confirmation required"
        )

    else:
        action = "WAIT — intraday indicators are mixed"

    return {
        "direction": direction,
        "signal": signal,
        "confidence": int(confidence),
        "long_score": int(long_score),
        "short_score": int(short_score),
        "score_spread": int(score_spread),
        "entry_ready": entry_ready,
        "action": action,

        "states": indicator_states,

        "values": {
            "close": close,
            "ema9": ema9,
            "ema20": ema20,
            "ema50": ema50,
            "stoch_k": stoch_k,
            "stoch_d": stoch_d,
            "wt1": wt1,
            "wt2": wt2,
            "supertrend": supertrend,
            "supertrend_direction": supertrend_direction,
            "vwap": vwap,
        },

        "bullish_reasons": bullish_reasons,
        "bearish_reasons": bearish_reasons,
        "warnings": warnings,
    }