from app.config import DEFAULT_TICKER

from app.market_data.stock_data import (
    get_historical_data,
)

from app.indicators.technical import (
    add_technical_indicators,
    add_advanced_indicators,
)

from app.indicators.obv import (
    add_obv,
    analyze_obv,
)


def main():

    ticker = DEFAULT_TICKER

    print("\n" + "=" * 70)
    print(f"OBV ANALYSIS: {ticker}")
    print("=" * 70)

    data = get_historical_data(
        ticker,
        period="5d",
        interval="5m",
    )

    data = add_technical_indicators(data)
    data = add_advanced_indicators(data)
    data = add_obv(data)

    row = data.iloc[-1]

    analysis = analyze_obv(
        row
    )

    print(
        f"Current Price:      "
        f"${row['Close']:.2f}"
    )

    print(
        f"OBV:                "
        f"{row['OBV']:,.0f}"
    )

    print(
        f"OBV Signal:         "
        f"{row['OBV_SIGNAL']:,.0f}"
    )

    print(
        f"OBV Change:         "
        f"{row['OBV_CHANGE']:+,.0f}"
    )

    print("-" * 70)

    print(
        f"Signal:             "
        f"{analysis['signal']}"
    )

    print(
        f"Direction:          "
        f"{analysis['direction']}"
    )

    print(
        f"Confidence:         "
        f"{analysis['confidence']}%"
    )

    print("-" * 70)

    print("Reasons:")

    for reason in analysis["reasons"]:
        print(f"- {reason}")

    if analysis["warnings"]:

        print("\nWarnings:")

        for warning in analysis["warnings"]:
            print(f"! {warning}")

    print("=" * 70)


if __name__ == "__main__":
    main()