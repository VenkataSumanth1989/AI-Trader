from app.market_data.gold_analysis import calculate_gold_analysis


def main():
    result = calculate_gold_analysis()

    print("\n" + "=" * 72)
    print("XAUUSD GOLD ANALYSIS")
    print("=" * 72)
    print(f"Latest Price:       ${result['quote']:.4f}")
    print(f"Latest Candle:      {result['quote_time']}")
    print(f"1-2 Day Bias:       {result['bias']}")
    print(f"Alignment:          {result['alignment']}%")
    print(
        f"Long vs Short:      "
        f"{result['long_score']}% / {result['short_score']}%"
    )
    print("-" * 72)

    for key, label in [("1h", "1 Hour"), ("4h", "4 Hour"), ("1d", "Daily")]:
        snap = result["snapshots"][key]
        print(
            f"{label:>7}: "
            f"Trend={snap['trend']} | "
            f"Direction={snap['direction']} | "
            f"RSI={snap['rsi']:.2f} | "
            f"MACD={snap['macd']} | "
            f"MSB={snap['msb']} | "
            f"Breakout={snap['breakout']}"
        )

    print("=" * 72)


if __name__ == "__main__":
    main()