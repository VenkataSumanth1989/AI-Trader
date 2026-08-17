from app.config import DEFAULT_TICKER

from app.market_data.stock_data import (
    get_historical_data,
)

from app.indicators.market_structure import (
    detect_market_structure_break,
)

from app.indicators.order_blocks import (
    detect_order_block,
)


def main():

    ticker = DEFAULT_TICKER

    print("\n" + "=" * 70)
    print(f"ORDER BLOCK ANALYSIS: {ticker}")
    print("=" * 70)

    data = get_historical_data(
        ticker,
        period="5d",
        interval="5m",
    )

    msb = detect_market_structure_break(
        data,
        swing_window=3,
        lookback=100,
    )

    print(
        f"MSB:                "
        f"{msb['msb']}"
    )

    print(
        f"MSB Direction:      "
        f"{msb['direction']}"
    )

    print("-" * 70)

    order_block = detect_order_block(
        data,
        msb,
        search_back=20,
    )

    print(
        f"Order Block:        "
        f"{order_block['order_block']}"
    )

    print(
        f"Direction:          "
        f"{order_block['direction']}"
    )

    print(
        f"Confidence:         "
        f"{order_block['confidence']}%"
    )

    print("-" * 70)

    if order_block["zone_low"] is not None:

        print(
            f"OB Low:             "
            f"${order_block['zone_low']:.2f}"
        )

        print(
            f"OB High:            "
            f"${order_block['zone_high']:.2f}"
        )

        print(
            f"OB Time:            "
            f"{order_block['ob_time']}"
        )

        print(
            f"Current Price:      "
            f"${order_block['current_price']:.2f}"
        )

        print(
            f"Price Position:     "
            f"{order_block['price_position']}"
        )

        print(
            f"Revisited:          "
            f"{order_block['revisited']}"
        )

    print("-" * 70)

    print("Reasons:")

    for reason in order_block["reasons"]:
        print(f"- {reason}")

    print("=" * 70)


if __name__ == "__main__":
    main()