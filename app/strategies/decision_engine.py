def make_final_decision(
    setup: dict,
    pullback: dict,
    confirmation: dict,
    risk_plan: dict,
    position: dict,
    risk_guard: dict,
) -> dict:
    """
    Combine all strategy components into one final decision.

    Critical components act as gates rather than simply
    adding their scores together.
    """

    reasons = []
    warnings = []

    # --------------------------------------------------
    # BASIC INFORMATION
    # --------------------------------------------------

    direction = setup.get("direction", "NEUTRAL")
    setup_type = setup.get("setup", "NO_SETUP")

    # --------------------------------------------------
    # RISK GUARD
    # --------------------------------------------------

    if not risk_guard.get("allowed", False):

        return {
            "decision": "NO_TRADE",
            "confidence": 0,
            "direction": direction,
            "setup": setup_type,
            "reasons": [
                risk_guard.get(
                    "reason",
                    "Risk guard blocked trading"
                )
            ],
            "warnings": [],
        }

    reasons.append("Risk guard allows trading")

    # --------------------------------------------------
    # SETUP GATE
    # --------------------------------------------------

    valid_setups = {
        "TREND_CONTINUATION",
        "HEALTHY_BULLISH_PULLBACK",
        "HEALTHY_BEARISH_PULLBACK",
    }

    if setup_type not in valid_setups:

        return {
            "decision": "WAIT",
            "confidence": setup.get(
                "confidence",
                0
            ),
            "direction": direction,
            "setup": setup_type,
            "reasons": [
                f"Setup {setup_type} is not entry-ready"
            ],
            "warnings": setup.get(
                "warnings",
                []
            ),
        }

    reasons.append(
        f"Valid setup detected: {setup_type}"
    )

    # --------------------------------------------------
    # ENTRY CONFIRMATION GATE
    # --------------------------------------------------

    if not confirmation.get("confirmed", False):

        return {
            "decision": "WAIT",
            "confidence": confirmation.get(
                "confidence",
                0
            ),
            "direction": confirmation.get(
                "direction",
                direction
            ),
            "setup": setup_type,
            "reasons": (
                reasons
                + confirmation.get(
                    "reasons",
                    []
                )
            ),
            "warnings": (
                confirmation.get(
                    "warnings",
                    []
                )
            ),
        }

    reasons.append("Entry confirmation passed")

    # --------------------------------------------------
    # RISK PLAN GATE
    # --------------------------------------------------

    if not risk_plan.get("valid", False):

        return {
            "decision": "NO_TRADE",
            "confidence": 0,
            "direction": direction,
            "setup": setup_type,
            "reasons": reasons,
            "warnings": [
                "Risk plan is invalid"
            ],
        }

    risk_reward = risk_plan.get(
        "risk_reward",
        0
    )

    if risk_reward < 1.5:

        return {
            "decision": "NO_TRADE",
            "confidence": 0,
            "direction": direction,
            "setup": setup_type,
            "reasons": reasons,
            "warnings": [
                "Risk/reward ratio is below 1:1.5"
            ],
        }

    reasons.append(
        f"Risk/reward acceptable: 1:{risk_reward:.2f}"
    )

    # --------------------------------------------------
    # POSITION SIZE GATE
    # --------------------------------------------------

    if not position.get("valid", False):

        return {
            "decision": "NO_TRADE",
            "confidence": 0,
            "direction": direction,
            "setup": setup_type,
            "reasons": reasons,
            "warnings": [
                position.get(
                    "reason",
                    "Position sizing failed"
                )
            ],
        }

    reasons.append(
        f"Position size valid: "
        f"{position['shares']} shares"
    )

    # --------------------------------------------------
    # FINAL DECISION
    # --------------------------------------------------

    if direction == "BULLISH":

        decision = "BUY"

    elif direction == "BEARISH":

        decision = "SELL"

    else:

        decision = "WAIT"

    # --------------------------------------------------
    # CONFIDENCE
    # --------------------------------------------------

    confidence_values = [
        setup.get("confidence", 0),
        confirmation.get("confidence", 0),
    ]

    confidence = int(
        sum(confidence_values)
        / len(confidence_values)
    )

    confidence = max(
        0,
        min(100, confidence)
    )

    return {
        "decision": decision,
        "confidence": confidence,
        "direction": direction,
        "setup": setup_type,
        "risk_reward": risk_reward,
        "position_size": position["shares"],
        "reasons": reasons,
        "warnings": warnings,
    }