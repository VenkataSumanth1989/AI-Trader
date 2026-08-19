from copy import deepcopy


def initial_trade_state():
    return {
        "state": "WAITING",
        "direction": "NONE",
        "consecutive_confirmations": 0,
        "required_confirmations": 2,
        "last_closed_candle": None,
        "entry_ready_since": None,
        "confidence": 0,
        "reason": "Waiting for closed-candle confirmation",
    }


def update_trade_state(
    previous_state: dict | None,
    confirmation: dict,
    closed_candle_time,
    keep_threshold: int = 60,
    required_confirmations: int = 2,
) -> dict:
    """
    Closed-candle trade-state machine.

    States:
        WAITING
        CANDIDATE
        ENTRY_READY
        INVALIDATED

    The state updates only once per newly completed candle.

    ENTRY_READY requires two consecutive completed candles with a confirmed
    entry in the same direction.

    Hysteresis:
        Once ENTRY_READY, a small confidence drop does not immediately cancel
        the signal. It remains ready while the same direction still has
        confidence >= keep_threshold. It is invalidated when confidence falls
        below that threshold or the direction flips.
    """

    state = deepcopy(previous_state) if previous_state else initial_trade_state()
    state["required_confirmations"] = required_confirmations

    candle_key = str(closed_candle_time)

    # Do not recalculate persistence repeatedly for the same closed candle.
    if state.get("last_closed_candle") == candle_key:
        return state

    state["last_closed_candle"] = candle_key

    confirmed = bool(confirmation.get("confirmed", False))
    direction = confirmation.get("direction", "NONE")
    confidence = int(confirmation.get("confidence", 0) or 0)

    previous_direction = state.get("direction", "NONE")
    previous_trade_state = state.get("state", "WAITING")

    # ----------------------------------------------------------
    # Already ENTRY_READY: apply hysteresis
    # ----------------------------------------------------------
    if previous_trade_state == "ENTRY_READY":
        same_direction = (
            direction == previous_direction
            or (
                direction == "NONE"
                and confidence >= keep_threshold
            )
        )

        if same_direction and confidence >= keep_threshold:
            state["confidence"] = confidence
            state["reason"] = (
                "Entry remains ready; closed-candle confidence is still "
                f"above the {keep_threshold}% keep threshold"
            )
            return state

        state["state"] = "INVALIDATED"
        state["confidence"] = confidence
        state["consecutive_confirmations"] = 0
        state["reason"] = (
            "Entry-ready signal invalidated because closed-candle confirmation "
            "lost strength or direction changed"
        )
        return state

    # ----------------------------------------------------------
    # New confirmed closed candle
    # ----------------------------------------------------------
    if confirmed and direction in ("LONG", "SHORT"):
        if previous_direction == direction:
            consecutive = state.get("consecutive_confirmations", 0) + 1
        else:
            consecutive = 1

        state["direction"] = direction
        state["consecutive_confirmations"] = consecutive
        state["confidence"] = confidence

        if consecutive >= required_confirmations:
            state["state"] = "ENTRY_READY"
            state["entry_ready_since"] = candle_key
            state["reason"] = (
                f"{required_confirmations} consecutive completed candles "
                f"confirmed the {direction} setup"
            )
        else:
            state["state"] = "CANDIDATE"
            state["reason"] = (
                f"{consecutive}/{required_confirmations} completed candles "
                f"confirmed the {direction} setup"
            )

        return state

    # ----------------------------------------------------------
    # Not confirmed
    # ----------------------------------------------------------
    if previous_trade_state == "INVALIDATED":
        state["state"] = "WAITING"

    else:
        state["state"] = "WAITING"

    state["direction"] = (
        direction if direction in ("LONG", "SHORT") else "NONE"
    )
    state["consecutive_confirmations"] = 0
    state["confidence"] = confidence
    state["entry_ready_since"] = None
    state["reason"] = "Waiting for a confirmed completed candle"

    return state