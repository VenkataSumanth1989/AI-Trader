from app.config import DEFAULT_TICKER

from app.market_data.stock_data import (
    get_historical_data,
)

from app.indicators.technical import (
    add_technical_indicators,
    add_advanced_indicators,
)

from app.indicators.market_structure import (
    detect_market_structure_break,
)


def main():

    ticker = DEFAULT_TICKER

    print("\n" + "=" * 70)
    print(f"MARKET STRUCTURE BREAK ANALYSIS: {ticker}")
    print("=" * 70)

    data = get_historical_data(
        ticker,
        period="5d",
        interval="5m",
    )

    data = add_technical_indicators(data)
    data = add_advanced_indicators(data)

    result = detect_market_structure_break(
        data,
        swing_window=3,
        lookback=100,
    )

    print(
        f"MSB:                "
        f"{result['msb']}"
    )

    print(
        f"Direction:          "
        f"{result['direction']}"
    )

    print(
        f"Confidence:         "
        f"{result['confidence']}%"
    )

    print("-" * 70)

    if result["break_level"] is not None:

        print(
            f"Break Level:        "
            f"${result['break_level']:.2f}"
        )

        print(
            f"Break Price:        "
            f"${result['break_price']:.2f}"
        )

        print(
            f"Swing Time:         "
            f"{result['swing_time']}"
        )

        print(
            f"Break Time:         "
            f"{result['break_time']}"
        )

    print("-" * 70)

    print("Reasons:")

    for reason in result["reasons"]:
        print(f"- {reason}")

    print("=" * 70)


if __name__ == "__main__":
    main()