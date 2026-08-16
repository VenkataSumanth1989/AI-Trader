def check_risk_guard(
    account_size: float,
    starting_day_equity: float,
    daily_pnl: float,
    consecutive_losses: int,
    max_daily_loss_percent: float = 2.0,
    max_consecutive_losses: int = 3,
) -> dict:
    """
    Protect the trading account from excessive daily losses.

    This function does NOT place or close trades.
    It only determines whether new trades should be allowed.
    """

    # --------------------------------------------------
    # VALIDATION
    # --------------------------------------------------

    if account_size <= 0:
        return {
            "allowed": False,
            "reason": "Invalid account size",
        }

    if starting_day_equity <= 0:
        return {
            "allowed": False,
            "reason": "Invalid starting day equity",
        }

    if max_daily_loss_percent <= 0:
        return {
            "allowed": False,
            "reason": "Invalid daily loss limit",
        }

    if max_consecutive_losses <= 0:
        return {
            "allowed": False,
            "reason": "Invalid consecutive loss limit",
        }

    # --------------------------------------------------
    # DAILY LOSS
    # --------------------------------------------------

    max_daily_loss = (
        starting_day_equity
        * max_daily_loss_percent
        / 100
    )

    # daily_pnl is negative when losing
    daily_loss = max(
        0.0,
        -daily_pnl
    )

    daily_loss_percent = (
        daily_loss
        / starting_day_equity
        * 100
    )

    # --------------------------------------------------
    # CHECK DAILY LOSS LIMIT
    # --------------------------------------------------

    if daily_loss >= max_daily_loss:

        return {
            "allowed": False,
            "reason": "MAX_DAILY_LOSS_REACHED",
            "daily_loss": round(daily_loss, 2),
            "daily_loss_percent": round(
                daily_loss_percent,
                3
            ),
            "max_daily_loss": round(
                max_daily_loss,
                2
            ),
        }

    # --------------------------------------------------
    # CHECK CONSECUTIVE LOSSES
    # --------------------------------------------------

    if consecutive_losses >= max_consecutive_losses:

        return {
            "allowed": False,
            "reason": "MAX_CONSECUTIVE_LOSSES_REACHED",
            "consecutive_losses": consecutive_losses,
            "max_consecutive_losses": max_consecutive_losses,
        }

    # --------------------------------------------------
    # REMAINING RISK
    # --------------------------------------------------

    remaining_daily_loss = (
        max_daily_loss - daily_loss
    )

    return {
        "allowed": True,
        "reason": "RISK_LIMITS_OK",
        "daily_loss": round(
            daily_loss,
            2
        ),
        "daily_loss_percent": round(
            daily_loss_percent,
            3
        ),
        "max_daily_loss": round(
            max_daily_loss,
            2
        ),
        "remaining_daily_loss": round(
            remaining_daily_loss,
            2
        ),
        "consecutive_losses": consecutive_losses,
        "max_consecutive_losses": max_consecutive_losses,
    }