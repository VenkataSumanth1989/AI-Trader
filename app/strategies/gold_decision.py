def calculate_gold_decision(gold_analysis: dict) -> dict:
    """
    Convert XAUUSD higher-timeframe analysis into a conservative decision state.

    Important:
    - Bias is NOT an entry signal.
    - READY requires higher-timeframe agreement plus 5m confirmation.
    - Overextended RSI and conflicting momentum can keep the setup in WATCH.
    """

    snapshots = gold_analysis["snapshots"]
    bias = gold_analysis.get("bias", "WAIT")

    s5 = snapshots["5m"]
    s1 = snapshots["1h"]
    s4 = snapshots["4h"]
    sd = snapshots["1d"]

    result = {
        "bias": bias,
        "trend_alignment": "MIXED",
        "entry_state": "WAIT",
        "candidate": "NONE",
        "confirmations": 0,
        "required_confirmations": 2,
        "reasons": [],
        "warnings": [],
        "entry_zone_low": None,
        "entry_zone_high": None,
        "invalidation": None,
        "target_1": None,
        "target_2": None,
        "risk_per_unit": None,
        "rr_1": None,
        "rr_2": None,
    }

    if bias not in ("LONG", "SHORT"):
        result["reasons"].append("Higher-timeframe bias is mixed.")
        return result

    # Higher-timeframe alignment label (not a probability).
    htf_states = [
        s4["trend"],
        sd["trend"],
        s4["direction"],
        sd["direction"],
        s4["msb_direction"],
        sd["msb_direction"],
    ]

    aligned = sum(1 for state in htf_states if state == ("BULLISH" if bias == "LONG" else "BEARISH"))

    if aligned >= 5:
        result["trend_alignment"] = "STRONG " + ("BULLISH" if bias == "LONG" else "BEARISH")
    elif aligned >= 3:
        result["trend_alignment"] = "MODERATE " + ("BULLISH" if bias == "LONG" else "BEARISH")
    else:
        result["trend_alignment"] = "WEAK / MIXED"

    result["candidate"] = bias

    # Warnings: overextension and conflicting 1H momentum.
    if bias == "LONG":
        if s4["rsi"] >= 70:
            result["warnings"].append(f"4H RSI is overbought at {s4['rsi']:.1f}.")
        if sd["rsi"] >= 70:
            result["warnings"].append(f"Daily RSI is overbought at {sd['rsi']:.1f}.")
        if s1["macd"] == "BEARISH":
            result["warnings"].append("1H MACD is bearish against the LONG bias.")
    else:
        if s4["rsi"] <= 30:
            result["warnings"].append(f"4H RSI is oversold at {s4['rsi']:.1f}.")
        if sd["rsi"] <= 30:
            result["warnings"].append(f"Daily RSI is oversold at {sd['rsi']:.1f}.")
        if s1["macd"] == "BULLISH":
            result["warnings"].append("1H MACD is bullish against the SHORT bias.")

    # 5-minute confirmation components.
    desired = "BULLISH" if bias == "LONG" else "BEARISH"

    checks = [
        ("5m EMA trend", s5["trend"] == desired),
        ("5m ADX/DI direction", s5["direction"] == desired),
        ("5m MACD", s5["macd"] == desired),
        ("5m Stochastic", s5["stochastic"] == desired),
        ("5m MSB", s5["msb_direction"] == desired),
    ]

    confirmations = sum(1 for _, passed in checks if passed)
    result["confirmations"] = confirmations

    for label, passed in checks:
        if passed:
            result["reasons"].append(f"{label} confirms {bias}.")
        else:
            result["warnings"].append(f"{label} does not confirm {bias}.")

    # Conservative READY rule:
    # - strong/moderate HTF alignment
    # - at least 4/5 entry checks
    # - no severe HTF overextension conflict
    severe_extension = (
        (bias == "LONG" and (s4["rsi"] >= 75 or sd["rsi"] >= 78))
        or
        (bias == "SHORT" and (s4["rsi"] <= 25 or sd["rsi"] <= 22))
    )

    if (
        confirmations >= 4
        and result["trend_alignment"] != "WEAK / MIXED"
        and not severe_extension
    ):
        result["entry_state"] = "READY"
    else:
        result["entry_state"] = "WATCH"

    # Trade plan based on 5m price/ATR plus nearest 1H/4H structure.
    price = float(s5["price"])
    atr = float(s5["atr"] or 0.0)
    band = max(atr * 0.30, price * 0.0005)

    result["entry_zone_low"] = price - band
    result["entry_zone_high"] = price + band

    if bias == "LONG":
        supports = [
            value for value in (s1.get("support"), s4.get("support"))
            if value is not None and value < price
        ]
        # Never allow structural support to create an unrealistically tight
        # XAUUSD stop. The invalidation must be at least 1.25 ATR below the
        # reference price, while still respecting nearby structure.
        minimum_atr_stop = price - max(atr * 1.25, price * 0.0025)

        if supports:
            structural_stop = (
                max(supports) - max(atr * 0.25, price * 0.0005)
            )
            invalidation = min(structural_stop, minimum_atr_stop)
        else:
            invalidation = minimum_atr_stop

        risk = price - invalidation
        if risk > 0:
            result["invalidation"] = invalidation
            result["target_1"] = price + risk * 1.5
            result["target_2"] = price + risk * 2.5
            result["risk_per_unit"] = risk
            result["rr_1"] = 1.5
            result["rr_2"] = 2.5

    else:
        resistances = [
            value for value in (s1.get("resistance"), s4.get("resistance"))
            if value is not None and value > price
        ]
        # Same protection for SHORT setups: invalidation must be at least
        # 1.25 ATR above the reference price and beyond nearby resistance.
        minimum_atr_stop = price + max(atr * 1.25, price * 0.0025)

        if resistances:
            structural_stop = (
                min(resistances) + max(atr * 0.25, price * 0.0005)
            )
            invalidation = max(structural_stop, minimum_atr_stop)
        else:
            invalidation = minimum_atr_stop

        risk = invalidation - price
        if risk > 0:
            result["invalidation"] = invalidation
            result["target_1"] = price - risk * 1.5
            result["target_2"] = price - risk * 2.5
            result["risk_per_unit"] = risk
            result["rr_1"] = 1.5
            result["rr_2"] = 2.5

    return result