import pandas as pd


def calculate_position_size(
    account_size: float,
    entry_price: float,
    stop_loss: float,
    risk_percent: float = 1.0,
    max_position_percent: float = 20.0,
) -> dict:
    """
    Calculate position size based on account risk.

    Risk is limited to risk_percent of account equity.

    A second limit prevents the position from becoming
    too large relative to the total account.

    This function does NOT place trades.
    """

    # --------------------------------------------------
    # VALIDATION
    # --------------------------------------------------

    if account_size <= 0:
        return {
            "valid": False,
            "reason": "Account size must be greater than zero",
        }

    if entry_price <= 0:
        return {
            "valid": False,
            "reason": "Entry price must be greater than zero",
        }

    if stop_loss <= 0:
        return {
            "valid": False,
            "reason": "Stop loss must be greater than zero",
        }

    if risk_percent <= 0:
        return {
            "valid": False,
            "reason": "Risk percentage must be greater than zero",
        }

    if max_position_percent <= 0:
        return {
            "valid": False,
            "reason": "Maximum position percentage must be greater than zero",
        }

    # --------------------------------------------------
    # RISK PER SHARE
    # --------------------------------------------------

    risk_per_share = abs(
        entry_price - stop_loss
    )

    if risk_per_share <= 0:
        return {
            "valid": False,
            "reason": "Entry and stop loss cannot be equal",
        }

    # --------------------------------------------------
    # MAXIMUM ACCOUNT RISK
    # --------------------------------------------------

    max_risk_amount = (
        account_size
        * risk_percent
        / 100
    )

    # --------------------------------------------------
    # POSITION SIZE BASED ON RISK
    # --------------------------------------------------

    risk_based_shares = int(
        max_risk_amount
        / risk_per_share
    )

    # --------------------------------------------------
    # MAXIMUM CAPITAL ALLOCATION
    # --------------------------------------------------

    max_position_value = (
        account_size
        * max_position_percent
        / 100
    )

    capital_based_shares = int(
        max_position_value
        / entry_price
    )

    # --------------------------------------------------
    # FINAL POSITION SIZE
    # --------------------------------------------------

    shares = min(
        risk_based_shares,
        capital_based_shares,
    )

    position_value = (
        shares
        * entry_price
    )

    actual_risk = (
        shares
        * risk_per_share
    )

    actual_risk_percent = (
        actual_risk
        / account_size
        * 100
    )

    # --------------------------------------------------
    # DECISION
    # --------------------------------------------------

    if shares <= 0:

        return {
            "valid": False,
            "reason": (
                "Account size is too small for the "
                "specified risk and position limits"
            ),
        }

    return {
        "valid": True,
        "account_size": round(account_size, 2),
        "entry_price": round(entry_price, 2),
        "stop_loss": round(stop_loss, 2),
        "risk_per_share": round(risk_per_share, 2),
        "risk_percent": round(risk_percent, 2),
        "max_risk_amount": round(max_risk_amount, 2),
        "max_position_percent": round(
            max_position_percent,
            2
        ),
        "max_position_value": round(
            max_position_value,
            2
        ),
        "shares": shares,
        "position_value": round(
            position_value,
            2
        ),
        "actual_risk": round(
            actual_risk,
            2
        ),
        "actual_risk_percent": round(
            actual_risk_percent,
            3
        ),
    }