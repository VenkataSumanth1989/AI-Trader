from app.config import DEFAULT_TICKER

from app.market_data.stock_data import get_historical_data

from app.indicators.technical import (
    add_technical_indicators,
    add_advanced_indicators,
)

from app.indicators.trend import (
    add_trend_indicators,
)

from app.strategies.setup_detector import (
    detect_setup,
)

from app.strategies.pullback_detector import (
    detect_pullback,
)

from app.strategies.entry_confirmation import (
    confirm_entry,
)

from app.strategies.risk_manager import (
    calculate_risk_plan,
)

from app.strategies.position_sizer import (
    calculate_position_size,
)

from app.strategies.risk_guard import (
    check_risk_guard,
)

from app.strategies.decision_engine import (
    make_final_decision,
)


def main():

    ticker = DEFAULT_TICKER

    print("\n" + "=" * 80)
    print(f"AI-TRADER FINAL ANALYSIS: {ticker}")
    print("=" * 80)

    # ==================================================
    # DAILY DATA
    # ==================================================

    daily = get_historical_data(
        ticker,
        period="1y",
        interval="1d",
    )

    daily = add_trend_indicators(daily)

    daily_latest = daily.iloc[-1]

    # ==================================================
    # INTRADAY DATA
    # ==================================================

    data = get_historical_data(
        ticker,
        period="5d",
        interval="5m",
    )

    data = add_technical_indicators(data)
    data = add_advanced_indicators(data)

    row = data.iloc[-1].copy()

    # Add daily trend indicators
    row["SMA_50"] = daily_latest["SMA_50"]
    row["SMA_200"] = daily_latest["SMA_200"]

    # ==================================================
    # SETUP DETECTION
    # ==================================================

    setup = detect_setup(row)

    # ==================================================
    # PULLBACK DETECTION
    # ==================================================

    pullback = detect_pullback(
        row,
        setup,
    )

    # ==================================================
    # ENTRY CONFIRMATION
    # ==================================================

    confirmation = confirm_entry(
        row,
        pullback,
    )

    # ==================================================
    # RISK PLAN + POSITION SIZE
    # ==================================================

    risk_plan = {
        "valid": False,
        "reason": "No confirmed entry",
    }

    position = {
        "valid": False,
        "shares": 0,
        "position_value": 0.0,
        "actual_risk": 0.0,
    }

    entry_confirmed = confirmation.get(
        "confirmed",
        False,
    )

    if entry_confirmed:

        direction = confirmation.get(
            "direction"
        )

        if direction in {"LONG", "SHORT"}:

            risk_plan = calculate_risk_plan(
                row,
                entry_price=float(row["Close"]),
                direction=direction,
                atr_multiplier=1.5,
                reward_risk_ratio=2.0,
            )

            if risk_plan["valid"]:

                position = calculate_position_size(
                    account_size=10_000,
                    entry_price=risk_plan["entry_price"],
                    stop_loss=risk_plan["stop_loss"],
                    risk_percent=1.0,
                    max_position_percent=20.0,
                )

    # ==================================================
    # RISK GUARD
    # ==================================================

    risk_guard = check_risk_guard(
        account_size=10_000,
        starting_day_equity=10_000,
        daily_pnl=0,
        consecutive_losses=0,
        max_daily_loss_percent=2.0,
        max_consecutive_losses=3,
    )

    # ==================================================
    # FINAL DECISION
    # ==================================================

    final = make_final_decision(
        setup=setup,
        pullback=pullback,
        confirmation=confirmation,
        risk_plan=risk_plan,
        position=position,
        risk_guard=risk_guard,
    )

    # ==================================================
    # MARKET DATA
    # ==================================================

    print("\n" + "-" * 80)
    print("MARKET DATA")
    print("-" * 80)

    print(
        f"Time:               "
        f"{data.index[-1]}"
    )

    print(
        f"Price:              "
        f"${row['Close']:.2f}"
    )

    print(
        f"Volume:             "
        f"{row['Volume']:,.0f}"
    )

    # ==================================================
    # TREND
    # ==================================================

    print("\n" + "-" * 80)
    print("TREND")
    print("-" * 80)

    print(
        f"EMA 9:              "
        f"${row['EMA_9']:.2f}"
    )

    print(
        f"EMA 20:             "
        f"${row['EMA_20']:.2f}"
    )

    print(
        f"EMA 50:             "
        f"${row['EMA_50']:.2f}"
    )

    print(
        f"SMA 50:             "
        f"${row['SMA_50']:.2f}"
    )

    print(
        f"SMA 200:            "
        f"${row['SMA_200']:.2f}"
    )

    print(
        f"VWAP:               "
        f"${row['VWAP']:.2f}"
    )

    # ==================================================
    # MOMENTUM
    # ==================================================

    print("\n" + "-" * 80)
    print("MOMENTUM")
    print("-" * 80)

    print(
        f"RSI 14:             "
        f"{row['RSI_14']:.2f}"
    )

    print(
        f"MACD:               "
        f"{row['MACD']:.4f}"
    )

    print(
        f"MACD Signal:        "
        f"{row['MACD_SIGNAL']:.4f}"
    )

    print(
        f"MACD Histogram:     "
        f"{row['MACD_HISTOGRAM']:.4f}"
    )

    print(
        f"Stochastic %K:      "
        f"{row['STOCH_K']:.2f}"
    )

    print(
        f"Stochastic %D:      "
        f"{row['STOCH_D']:.2f}"
    )

    # ==================================================
    # TREND STRENGTH / VOLUME
    # ==================================================

    print("\n" + "-" * 80)
    print("TREND STRENGTH / VOLUME")
    print("-" * 80)

    print(
        f"ATR 14:             "
        f"{row['ATR_14']:.2f}"
    )

    print(
        f"ADX 14:             "
        f"{row['ADX_14']:.2f}"
    )

    print(
        f"DI+ 14:             "
        f"{row['DI_PLUS_14']:.2f}"
    )

    print(
        f"DI- 14:             "
        f"{row['DI_MINUS_14']:.2f}"
    )

    print(
        f"Relative Volume:    "
        f"{row['RELATIVE_VOLUME']:.2f}x"
    )

    # ==================================================
    # AI-TRADER ANALYSIS
    # ==================================================

    print("\n" + "=" * 80)
    print("AI-TRADER ANALYSIS")
    print("=" * 80)

    print(
        f"Market Regime:      "
        f"{setup['market_regime']}"
    )

    print(
        f"Direction:          "
        f"{setup['direction']}"
    )

    print(
        f"Setup:              "
        f"{setup['setup']}"
    )

    print(
        f"Pullback:           "
        f"{pullback['type']}"
    )

    print(
        f"Entry Confirmation: "
        f"{confirmation['decision']}"
    )

    print(
        f"Setup Confidence:   "
        f"{setup['confidence']}%"
    )

    print(
        f"Entry Confidence:   "
        f"{confirmation['confidence']}%"
    )

    # ==================================================
    # RISK MANAGEMENT
    # ==================================================

    print("\n" + "-" * 80)
    print("RISK MANAGEMENT")
    print("-" * 80)

    if risk_plan["valid"]:

        print(
            f"Entry:              "
            f"${risk_plan['entry_price']:.2f}"
        )

        print(
            f"Stop Loss:          "
            f"${risk_plan['stop_loss']:.2f}"
        )

        print(
            f"Target:             "
            f"${risk_plan['target']:.2f}"
        )

        print(
            f"Risk / Share:       "
            f"${risk_plan['risk_per_share']:.2f}"
        )

        print(
            f"Risk / Reward:      "
            f"1:{risk_plan['risk_reward']:.2f}"
        )

        print(
            f"Risk Quality:       "
            f"{risk_plan['quality']}"
        )

    else:

        print(
            "Risk Plan:          "
            "NOT GENERATED"
        )

        print(
            f"Reason:             "
            f"{risk_plan['reason']}"
        )

    # ==================================================
    # POSITION SIZE
    # ==================================================

    if position.get("valid", False):

        print(
            f"Position Size:      "
            f"{position['shares']} shares"
        )

        print(
            f"Position Value:     "
            f"${position['position_value']:,.2f}"
        )

        print(
            f"Actual Risk:        "
            f"${position['actual_risk']:.2f}"
        )

    else:

        print(
            "Position Size:      "
            "0 shares"
        )

        print(
            "Trade Status:       "
            "NO CONFIRMED ENTRY"
        )

    # ==================================================
    # SETUP REASONS
    # ==================================================

    print("\n" + "-" * 80)
    print("SETUP REASONS")
    print("-" * 80)

    for reason in setup.get(
        "reasons",
        [],
    ):

        print(
            f"- {reason}"
        )

    # ==================================================
    # PULLBACK REASONS
    # ==================================================

    pullback_reasons = pullback.get(
        "reasons",
        [],
    )

    if pullback_reasons:

        print("\nPULLBACK ANALYSIS")

        for reason in pullback_reasons:

            print(
                f"- {reason}"
            )

    # ==================================================
    # ENTRY CONFIRMATION REASONS
    # ==================================================

    confirmation_reasons = confirmation.get(
        "reasons",
        [],
    )

    if confirmation_reasons:

        print("\nENTRY CONFIRMATION")

        for reason in confirmation_reasons:

            print(
                f"- {reason}"
            )

    # ==================================================
    # WARNINGS
    # ==================================================

    warnings = (
        setup.get("warnings", [])
        + pullback.get("warnings", [])
        + confirmation.get("warnings", [])
    )

    if warnings:

        print("\nWARNINGS")

        for warning in warnings:

            print(
                f"! {warning}"
            )

    # ==================================================
    # FINAL DECISION
    # ==================================================

    print("\n" + "=" * 80)
    print("FINAL DECISION")
    print("=" * 80)

    print(
        f"Decision:           "
        f"{final['decision']}"
    )

    print(
        f"Confidence:         "
        f"{final['confidence']}%"
    )

    print(
        f"Direction:          "
        f"{final['direction']}"
    )

    print(
        f"Setup:              "
        f"{final['setup']}"
    )

    if final.get("risk_reward") is not None:

        print(
            f"Risk / Reward:      "
            f"1:{final['risk_reward']:.2f}"
        )

    if final.get("position_size") is not None:

        print(
            f"Position Size:      "
            f"{final['position_size']} shares"
        )

    # ==================================================
    # FINAL REASONS
    # ==================================================

    if final.get("reasons"):

        print("\nFINAL DECISION REASONS")

        for reason in final["reasons"]:

            print(
                f"- {reason}"
            )

    if final.get("warnings"):

        print("\nFINAL WARNINGS")

        for warning in final["warnings"]:

            print(
                f"! {warning}"
            )

    print("=" * 80)


if __name__ == "__main__":
    main()