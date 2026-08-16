from app.config import DEFAULT_TICKER

from app.market_data.stock_data import (
    get_historical_data,
)

from app.indicators.technical import (
    add_technical_indicators,
    add_advanced_indicators,
)

from app.indicators.bollinger_bands import (
    add_bollinger_bands,
    analyze_bollinger_bands,
)


def main():

    ticker = DEFAULT_TICKER

    print("\n" + "=" * 70)
    print(f"BOLLINGER BAND ANALYSIS: {ticker}")
    print("=" * 70)

    data = get_historical_data(
        ticker,
        period="5d",
        interval="5m",
    )

    data = add_technical_indicators(data)
    data = add_advanced_indicators(data)
    data = add_bollinger_bands(data)

    row = data.iloc[-1]

    analysis = analyze_bollinger_bands(
        row
    )

    print(
        f"Current Price:      "
        f"${row['Close']:.2f}"
    )

    print(
        f"Upper Band:         "
        f"${row['BB_UPPER']:.2f}"
    )

    print(
        f"Middle Band:        "
        f"${row['BB_MIDDLE']:.2f}"
    )

    print(
        f"Lower Band:         "
        f"${row['BB_LOWER']:.2f}"
    )

    print(
        f"Band Width:         "
        f"{row['BB_WIDTH']:.2f}%"
    )

    print(
        f"%B:                 "
        f"{row['BB_PERCENT_B']:.2f}"
    )

    print("-" * 70)

    print(
        f"Signal:             "
        f"{analysis['signal']}"
    )

    print(
        f"Position:           "
        f"{analysis['position']}"
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