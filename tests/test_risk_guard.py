from app.strategies.risk_guard import check_risk_guard


def run_test(
    title,
    daily_pnl,
    consecutive_losses,
):

    result = check_risk_guard(
        account_size=10_000,
        starting_day_equity=10_000,
        daily_pnl=daily_pnl,
        consecutive_losses=consecutive_losses,
        max_daily_loss_percent=2.0,
        max_consecutive_losses=3,
    )

    print("\n" + "-" * 70)
    print(title)
    print("-" * 70)

    print(f"Allowed:             {result['allowed']}")
    print(f"Reason:              {result['reason']}")

    if "daily_loss" in result:

        print(
            f"Daily Loss:          "
            f"${result['daily_loss']:.2f}"
        )

        if "remaining_daily_loss" in result:

            print(
                f"Remaining Daily Risk: "
                f"${result['remaining_daily_loss']:.2f}"
            )

    if "consecutive_losses" in result:

        print(
            f"Consecutive Losses:  "
            f"{result['consecutive_losses']}"
        )


def main():

    print("\n" + "=" * 70)
    print("AI-TRADER RISK GUARD TEST")
    print("=" * 70)

    # --------------------------------------------------
    # TEST 1
    # --------------------------------------------------

    run_test(
        "TEST 1: NORMAL",
        daily_pnl=50,
        consecutive_losses=0,
    )

    # --------------------------------------------------
    # TEST 2
    # --------------------------------------------------

    run_test(
        "TEST 2: DAILY LOSS WITHIN LIMIT",
        daily_pnl=-100,
        consecutive_losses=1,
    )

    # --------------------------------------------------
    # TEST 3
    # --------------------------------------------------

    run_test(
        "TEST 3: MAX DAILY LOSS",
        daily_pnl=-200,
        consecutive_losses=2,
    )

    # --------------------------------------------------
    # TEST 4
    # --------------------------------------------------

    run_test(
        "TEST 4: MAX CONSECUTIVE LOSSES",
        daily_pnl=-50,
        consecutive_losses=3,
    )

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()