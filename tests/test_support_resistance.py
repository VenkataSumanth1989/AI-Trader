from app.config import DEFAULT_TICKER

from app.market_data.stock_data import (
    get_historical_data,
)

from app.indicators.support_resistance import (
    detect_support_resistance,
)


def main():
    ticker = DEFAULT_TICKER

    print("\n" + "=" * 72)
    print(f"SUPPORT / RESISTANCE ANALYSIS: {ticker}")
    print("=" * 72)

    data = get_historical_data(
        ticker,
        period="5d",
        interval="5m",
    )

    result = detect_support_resistance(
        data,
        lookback=120,
        swing_window=3,
        tolerance_percent=0.30,
    )

    print(f"Current Price:       ${result['price']:.2f}")
    print("-" * 72)

    if result["support"] is not None:
        print(f"Support:             ${result['support']:.2f}")
        print(f"Support Touches:     {result['support_touches']}")
        print(
            f"Support Distance:    "
            f"{result['support_distance_percent']:+.2f}%"
        )

    if result["resistance"] is not None:
        print(f"Resistance:          ${result['resistance']:.2f}")
        print(f"Resistance Touches:  {result['resistance_touches']}")
        print(
            f"Resistance Distance: "
            f"{result['resistance_distance_percent']:+.2f}%"
        )

    print("-" * 72)
    print(f"Position:            {result['position']}")
    print(f"Breakout:            {result['breakout']}")

    if result["breakout_level"] is not None:
        print(f"Breakout Level:      ${result['breakout_level']:.2f}")
        print(
            f"Breakout Distance:   "
            f"{result['breakout_distance_percent']:+.2f}%"
        )

    print(f"Confidence:          {result['confidence']}%")

    print("-" * 72)
    print("Reasons:")

    for reason in result["reasons"]:
        print(f"- {reason}")

    if result["warnings"]:
        print("-" * 72)
        print("Warnings:")
        for warning in result["warnings"]:
            print(f"- {warning}")

    print("=" * 72)


if __name__ == "__main__":
    main()