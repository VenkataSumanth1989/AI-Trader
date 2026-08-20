def build_trade_plan(
    *,
    swing_outlook: dict,
    trade_state: dict,
    row,
    multi_timeframe: dict,
) -> dict:
    """
    Build a conservative 1–2 day trade plan from signals AI-Trader already has.

    READY:
        Swing bias and closed-candle ENTRY_READY agree.

    WATCH:
        LONG/SHORT bias exists, but closed-candle entry is not ready.

    INVALID:
        Entry state conflicts with or invalidates the swing bias.

    NO_SETUP:
        No clear LONG/SHORT swing bias.

    The plan uses 5-minute ATR plus 1H/4H support/resistance.
    """

    bias = swing_outlook.get("bias", "WAIT")
    state = trade_state.get("state", "WAITING")
    candidate = trade_state.get("direction", "NONE")

    close_price = float(row["Close"])
    atr = float(row.get("ATR_14", 0) or 0)

    snapshots = multi_timeframe.get("snapshots", {})
    one_hour = snapshots.get("1h", {})
    four_hour = snapshots.get("4h", {})

    result = {
        "bias": bias,
        "status": "NO_SETUP",
        "entry_zone_low": None,
        "entry_zone_high": None,
        "planned_entry": None,
        "invalidation": None,
        "target_1": None,
        "target_2": None,
        "risk_per_share": None,
        "risk_reward_1": None,
        "risk_reward_2": None,
        "trigger": "No trade plan yet",
        "reasons": [],
        "warnings": [],
    }

    if bias not in ("LONG", "SHORT"):
        result["reasons"].append(
            "No clear 1–2 day LONG or SHORT bias is currently available."
        )
        return result

    if state == "INVALIDATED":
        status = "INVALID"
    elif state == "ENTRY_READY" and candidate == bias:
        status = "READY"
    elif (
        candidate in ("LONG", "SHORT")
        and candidate != bias
        and state in ("CANDIDATE", "ENTRY_READY")
    ):
        status = "INVALID"
    else:
        status = "WATCH"

    result["status"] = status

    # Small ATR-based entry band around the last completed 5-minute close.
    band = (
        max(atr * 0.30, close_price * 0.001)
        if atr > 0
        else close_price * 0.0025
    )

    result["entry_zone_low"] = close_price - band
    result["entry_zone_high"] = close_price + band
    result["planned_entry"] = close_price

    if bias == "LONG":
        supports = [
            value
            for value in (
                one_hour.get("support"),
                four_hour.get("support"),
            )
            if value is not None and value < close_price
        ]

        if supports:
            support = max(supports)
            invalidation = support - max(atr * 0.25, close_price * 0.001)
            result["reasons"].append(
                "Invalidation is below the nearest useful 1H/4H support."
            )
        else:
            invalidation = close_price - max(atr * 1.5, close_price * 0.01)
            result["warnings"].append(
                "No useful support below entry; ATR fallback is used."
            )

        risk = close_price - invalidation

        if risk <= 0:
            result["status"] = "INVALID"
            result["warnings"].append(
                "A valid LONG invalidation level could not be generated."
            )
            return result

        target_1 = close_price + (risk * 1.5)
        target_2 = close_price + (risk * 2.5)

        result["trigger"] = (
            "LONG entry conditions are confirmed; avoid chasing outside the entry zone."
            if status == "READY"
            else "Wait for LONG closed-candle confirmation before entering."
        )

    else:
        resistances = [
            value
            for value in (
                one_hour.get("resistance"),
                four_hour.get("resistance"),
            )
            if value is not None and value > close_price
        ]

        if resistances:
            resistance = min(resistances)
            invalidation = resistance + max(atr * 0.25, close_price * 0.001)
            result["reasons"].append(
                "Invalidation is above the nearest useful 1H/4H resistance."
            )
        else:
            invalidation = close_price + max(atr * 1.5, close_price * 0.01)
            result["warnings"].append(
                "No useful resistance above entry; ATR fallback is used."
            )

        risk = invalidation - close_price

        if risk <= 0:
            result["status"] = "INVALID"
            result["warnings"].append(
                "A valid SHORT invalidation level could not be generated."
            )
            return result

        target_1 = close_price - (risk * 1.5)
        target_2 = close_price - (risk * 2.5)

        result["trigger"] = (
            "SHORT entry conditions are confirmed; avoid chasing outside the entry zone."
            if status == "READY"
            else "Wait for SHORT closed-candle confirmation before entering."
        )

    result.update(
        {
            "invalidation": invalidation,
            "target_1": target_1,
            "target_2": target_2,
            "risk_per_share": risk,
            "risk_reward_1": 1.5,
            "risk_reward_2": 2.5,
        }
    )

    result["reasons"].append(f"1–2 day swing bias is {bias}.")

    if status == "READY":
        result["reasons"].append(
            "Closed-candle trade state is ENTRY READY in the same direction."
        )
    elif status == "WATCH":
        result["reasons"].append(
            "Bias exists, but entry confirmation is not ready yet."
        )
    elif status == "INVALID":
        result["warnings"].append(
            "Current closed-candle state conflicts with or invalidates the swing bias."
        )

    result["reasons"].append(
        "Targets are fixed at 1.5R and 2.5R to keep the plan transparent."
    )

    return result