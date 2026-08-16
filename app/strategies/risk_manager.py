import pandas as pd


def calculate_risk_plan(
    row: pd.Series,
    entry_price: float | None = None,
    direction: str = "LONG",
    atr_multiplier: float = 1.5,
    reward_risk_ratio: float = 2.0,
) -> dict:
    """
    Calculate stop-loss, target and risk/reward.

    Uses ATR to adapt the stop distance to current volatility.

    This function does NOT place trades.
    """

    if entry_price is None:
        entry_price = float(row["Close"])

    atr = float(row["ATR_14"])

    if pd.isna(atr) or atr <= 0:
        return {
            "valid": False,
            "reason": "ATR unavailable or invalid",
        }

    entry_price = float(entry_price)

    # --------------------------------------------------
    # LONG
    # --------------------------------------------------

    if direction == "LONG":

        stop_distance = atr * atr_multiplier

        stop_loss = entry_price - stop_distance

        risk_per_share = entry_price - stop_loss

        target = (
            entry_price
            + risk_per_share * reward_risk_ratio
        )

    # --------------------------------------------------
    # SHORT
    # --------------------------------------------------

    elif direction == "SHORT":

        stop_distance = atr * atr_multiplier

        stop_loss = entry_price + stop_distance

        risk_per_share = stop_loss - entry_price

        target = (
            entry_price
            - risk_per_share * reward_risk_ratio
        )

    else:

        return {
            "valid": False,
            "reason": "Invalid trade direction",
        }

    # --------------------------------------------------
    # RISK / REWARD
    # --------------------------------------------------

    if risk_per_share <= 0:

        return {
            "valid": False,
            "reason": "Invalid risk calculation",
        }

    actual_reward = abs(
        target - entry_price
    )

    risk_reward = (
        actual_reward / risk_per_share
    )

    # --------------------------------------------------
    # QUALITY
    # --------------------------------------------------

    if risk_reward >= 3.0:
        quality = "EXCELLENT"

    elif risk_reward >= 2.0:
        quality = "GOOD"

    elif risk_reward >= 1.5:
        quality = "ACCEPTABLE"

    else:
        quality = "POOR"

    return {
        "valid": True,
        "direction": direction,
        "entry_price": round(entry_price, 2),
        "atr": round(atr, 2),
        "atr_multiplier": atr_multiplier,
        "stop_loss": round(stop_loss, 2),
        "target": round(target, 2),
        "risk_per_share": round(risk_per_share, 2),
        "reward_per_share": round(actual_reward, 2),
        "risk_reward": round(risk_reward, 2),
        "quality": quality,
    }