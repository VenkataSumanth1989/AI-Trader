from app.strategies.trade_state import (
    initial_trade_state,
    update_trade_state,
)


def confirmation(confirmed, direction, confidence):
    return {
        "confirmed": confirmed,
        "direction": direction,
        "confidence": confidence,
    }


def main():
    state = initial_trade_state()

    state = update_trade_state(
        state,
        confirmation(True, "LONG", 82),
        "2026-08-19 09:45:00-04:00",
    )
    print("Candle 1:", state["state"], state["consecutive_confirmations"])

    state = update_trade_state(
        state,
        confirmation(True, "LONG", 84),
        "2026-08-19 09:50:00-04:00",
    )
    print("Candle 2:", state["state"], state["consecutive_confirmations"])

    state = update_trade_state(
        state,
        confirmation(False, "LONG", 68),
        "2026-08-19 09:55:00-04:00",
    )
    print("Small drop:", state["state"], state["confidence"])

    state = update_trade_state(
        state,
        confirmation(False, "LONG", 55),
        "2026-08-19 10:00:00-04:00",
    )
    print("Invalidated:", state["state"], state["confidence"])


if __name__ == "__main__":
    main()