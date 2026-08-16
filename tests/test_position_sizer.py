from app.config import DEFAULT_TICKER
from app.market_data.stock_data import get_historical_data
from app.indicators.technical import (
    add_technical_indicators,
    add_advanced_indicators,
)
from app.strategies.risk_manager import calculate_risk_plan
from app.strategies.position_sizer import calculate_position_size


def main():

    ticker = DEFAULT_TICKER

    # Sample account for testing only.
    account_size = 10_000.0

    print("\n" + "=" * 70)
    print(f"AI-TRADER POSITION SIZING: {ticker}")
    print("=" * 70)

    # --------------------------------------------------
    # MARKET DATA
    # --------------------------------------------------

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
    # RISK PLAN
    # --------------------------------------------------

    risk_plan = calculate_risk_plan(
        row,
        entry_price=entry_price,
        direction="LONG",
        atr_multiplier=1.5,
        reward_risk_ratio=2.0,
    )

    if not risk_plan["valid"]:

        print("Risk plan invalid:")
        print(risk_plan["reason"])
        return

    # --------------------------------------------------
    # POSITION SIZE
    # --------------------------------------------------

    position = calculate_position_size(
        account_size=account_size,
        entry_price=risk_plan["entry_price"],
        stop_loss=risk_plan["stop_loss"],
        risk_percent=1.0,
        max_position_percent=20.0,
    )

    print(f"Account Size:       ${account_size:,.2f}")
    print(f"Entry Price:        ${risk_plan['entry_price']:.2f}")
    print(f"Stop Loss:          ${risk_plan['stop_loss']:.2f}")
    print("-" * 70)

    if position["valid"]:

        print(f"Risk / Share:       ${position['risk_per_share']:.2f}")
        print(f"Maximum Risk:       ${position['max_risk_amount']:.2f}")
        print(f"Shares:             {position['shares']}")
        print(f"Position Value:     ${position['position_value']:,.2f}")
        print(f"Actual Risk:        ${position['actual_risk']:.2f}")
        print(
            f"Actual Risk %:      "
            f"{position['actual_risk_percent']:.3f}%"
        )

    else:

        print("Position sizing failed:")
        print(position["reason"])

    print("=" * 70)


if __name__ == "__main__":
    main()