from app.config import DEFAULT_TICKER
from app.market_data.stock_data import get_historical_data
from app.indicators.technical import (
    add_technical_indicators,
    add_advanced_indicators,
)
from app.strategies.risk_manager import calculate_risk_plan


def main():

    ticker = DEFAULT_TICKER

    print("\n" + "=" * 70)
    print(f"AI-TRADER RISK ANALYSIS: {ticker}")
    print("=" * 70)

    # Get intraday data
    data = get_historical_data(
        ticker,
        period="5d",
        interval="5m"
    )

    data = add_technical_indicators(data)
    data = add_advanced_indicators(data)

    row = data.iloc[-1]

    entry_price = float(row["Close"])

    # --------------------------------------------------
    # LONG RISK PLAN
    # --------------------------------------------------

    long_plan = calculate_risk_plan(
        row,
        entry_price=entry_price,
        direction="LONG",
        atr_multiplier=1.5,
        reward_risk_ratio=2.0,
    )

    # --------------------------------------------------
    # SHORT RISK PLAN
    # --------------------------------------------------

    short_plan = calculate_risk_plan(
        row,
        entry_price=entry_price,
        direction="SHORT",
        atr_multiplier=1.5,
        reward_risk_ratio=2.0,
    )

    print(f"Current Price:      ${entry_price:.2f}")
    print(f"ATR 14:             ${row['ATR_14']:.2f}")

    print("\n" + "-" * 70)
    print("LONG RISK PLAN")
    print("-" * 70)

    if long_plan["valid"]:

        print(f"Entry:              ${long_plan['entry_price']:.2f}")
        print(f"Stop Loss:          ${long_plan['stop_loss']:.2f}")
        print(f"Target:             ${long_plan['target']:.2f}")
        print(f"Risk / Share:       ${long_plan['risk_per_share']:.2f}")
        print(f"Reward / Share:     ${long_plan['reward_per_share']:.2f}")
        print(f"Risk / Reward:      1:{long_plan['risk_reward']:.2f}")
        print(f"Quality:            {long_plan['quality']}")

    else:

        print(f"Invalid: {long_plan['reason']}")

    print("\n" + "-" * 70)
    print("SHORT RISK PLAN")
    print("-" * 70)

    if short_plan["valid"]:

        print(f"Entry:              ${short_plan['entry_price']:.2f}")
        print(f"Stop Loss:          ${short_plan['stop_loss']:.2f}")
        print(f"Target:             ${short_plan['target']:.2f}")
        print(f"Risk / Share:       ${short_plan['risk_per_share']:.2f}")
        print(f"Reward / Share:     ${short_plan['reward_per_share']:.2f}")
        print(f"Risk / Reward:      1:{short_plan['risk_reward']:.2f}")
        print(f"Quality:            {short_plan['quality']}")

    else:

        print(f"Invalid: {short_plan['reason']}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()