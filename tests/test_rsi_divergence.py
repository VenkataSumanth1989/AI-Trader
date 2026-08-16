from app.config import DEFAULT_TICKER

from app.market_data.stock_data import (
    get_historical_data,
)

from app.indicators.technical import (
    add_technical_indicators,
    add_advanced_indicators,
)

from app.indicators.rsi_divergence import (
    detect_rsi_divergence,
)


def main():

    ticker = DEFAULT_TICKER

    print("\n" + "=" * 70)
    print(f"RSI DIVERGENCE ANALYSIS: {ticker}")
    print("=" * 70)

    data = get_historical_data(
        ticker,
        period="5d",
        interval="5m",
    )

    data = add_technical_indicators(data)
    data = add_advanced_indicators(data)

    result = detect_rsi_divergence(
        data,
        lookback=60,
        swing_window=3,
    )

    print(f"Divergence:         {result['divergence']}")
    print(f"Direction:          {result['direction']}")
    print(f"Confidence:         {result['confidence']}%")

    print("-" * 70)

    if result.get("price_point_1") is not None:

        print(
            f"Price Point 1:      "
            f"${result['price_point_1']:.2f}"
        )

        print(
            f"Price Point 2:      "
            f"${result['price_point_2']:.2f}"
        )

        print(
            f"RSI Point 1:        "
            f"{result['rsi_point_1']:.2f}"
        )

        print(
            f"RSI Point 2:        "
            f"{result['rsi_point_2']:.2f}"
        )

        print(
            f"Time Point 1:       "
            f"{result['time_point_1']}"
        )

        print(
            f"Time Point 2:       "
            f"{result['time_point_2']}"
        )

    print("-" * 70)

    print("Reasons:")

    for reason in result.get(
        "reasons",
        [],
    ):
        print(f"- {reason}")

    print("=" * 70)


if __name__ == "__main__":
    main()