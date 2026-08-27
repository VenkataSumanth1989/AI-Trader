import math


def _safe_float(value):
    try:
        value = float(value)
        return value if math.isfinite(value) else None
    except (TypeError, ValueError):
        return None


def build_intraday_trade_plan(
    intraday_signal,
    row,
    recent_data=None,
):
    """
    Build an intraday trade plan from the completed 5-minute candle.

    IMPORTANT:
    - Independent from the 1–2 day swing trade plan.
    - Uses the intraday engine direction.
    - Uses ATR and recent 5-minute structure for invalidation.
    - T1 = 1.5R
    - T2 = 2.5R
    - Returns NO_SETUP when intraday direction is WAIT.
    """

    direction = intraday_signal.get("direction", "WAIT")
    confidence = intraday_signal.get("confidence", 0)
    entry_ready = intraday_signal.get("entry_ready", False)

    close = _safe_float(row.get("Close"))
    ema9 = _safe_float(row.get("EMA_9"))
    vwap = _safe_float(row.get("VWAP"))
    atr = _safe_float(row.get("ATR_14"))

    # --------------------------------------------------------
    # Basic validation
    # --------------------------------------------------------

    if (
        direction not in ("LONG", "SHORT")
        or close is None
        or atr is None
        or atr <= 0
    ):
        return {
            "status": "NO_SETUP",
            "direction": "NONE",
            "entry_low": None,
            "entry_high": None,
            "invalidation": None,
            "target1": None,
            "target2": None,
            "risk_per_share": None,
            "rr1": None,
            "rr2": None,
            "reason": (
                "No valid intraday directional setup yet."
            ),
        }

    # --------------------------------------------------------
    # Recent 5-minute structure
    # --------------------------------------------------------

    recent_high = None
    recent_low = None

    if recent_data is not None and len(recent_data) >= 3:

        structure_data = recent_data.tail(12)

        try:
            recent_high = float(
                structure_data["High"].max()
            )

            recent_low = float(
                structure_data["Low"].min()
            )

        except Exception:
            recent_high = None
            recent_low = None

    # --------------------------------------------------------
    # Entry reference
    # --------------------------------------------------------

    references = [
        value
        for value in (close, ema9, vwap)
        if value is not None
    ]

    entry_reference = (
        sum(references) / len(references)
        if references
        else close
    )

    # Keep entry zone fairly tight for intraday trading.
    zone_half_width = atr * 0.15

    entry_low = entry_reference - zone_half_width
    entry_high = entry_reference + zone_half_width

    # --------------------------------------------------------
    # LONG PLAN
    # --------------------------------------------------------

    if direction == "LONG":

        structure_stop = (
            recent_low - atr * 0.10
            if recent_low is not None
            else close - atr
        )

        atr_stop = entry_reference - atr

        # For LONG, invalidation must be below entry.
        invalidation = min(
            structure_stop,
            atr_stop,
        )

        risk = entry_reference - invalidation

        if risk <= 0:
            return {
                "status": "NO_SETUP",
                "direction": "NONE",
                "entry_low": None,
                "entry_high": None,
                "invalidation": None,
                "target1": None,
                "target2": None,
                "risk_per_share": None,
                "rr1": None,
                "rr2": None,
                "reason": "Invalid LONG risk geometry.",
            }

        target1 = entry_reference + risk * 1.5
        target2 = entry_reference + risk * 2.5

    # --------------------------------------------------------
    # SHORT PLAN
    # --------------------------------------------------------

    else:

        structure_stop = (
            recent_high + atr * 0.10
            if recent_high is not None
            else close + atr
        )

        atr_stop = entry_reference + atr

        # For SHORT, invalidation must be above entry.
        invalidation = max(
            structure_stop,
            atr_stop,
        )

        risk = invalidation - entry_reference

        if risk <= 0:
            return {
                "status": "NO_SETUP",
                "direction": "NONE",
                "entry_low": None,
                "entry_high": None,
                "invalidation": None,
                "target1": None,
                "target2": None,
                "risk_per_share": None,
                "rr1": None,
                "rr2": None,
                "reason": "Invalid SHORT risk geometry.",
            }

        target1 = entry_reference - risk * 1.5
        target2 = entry_reference - risk * 2.5

    # --------------------------------------------------------
    # Status
    # --------------------------------------------------------

    if entry_ready:
        status = "READY"

    elif confidence >= 70:
        status = "WATCH"

    else:
        status = "EARLY"

    return {
        "status": status,
        "direction": direction,

        "entry_reference": round(
            entry_reference,
            4,
        ),

        "entry_low": round(
            entry_low,
            4,
        ),

        "entry_high": round(
            entry_high,
            4,
        ),

        "invalidation": round(
            invalidation,
            4,
        ),

        "target1": round(
            target1,
            4,
        ),

        "target2": round(
            target2,
            4,
        ),

        "risk_per_share": round(
            risk,
            4,
        ),

        "rr1": 1.5,
        "rr2": 2.5,

        "atr": round(
            atr,
            4,
        ),

        "recent_high": (
            round(recent_high, 4)
            if recent_high is not None
            else None
        ),

        "recent_low": (
            round(recent_low, 4)
            if recent_low is not None
            else None
        ),

        "reason": (
            f"{direction} intraday plan based on completed "
            "5-minute candle, ATR and recent 5-minute structure."
        ),
    }