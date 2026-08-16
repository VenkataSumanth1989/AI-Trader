from app.config import DEFAULT_TICKER

from app.market_data.stock_data import (
    get_historical_data,
    get_daily_data,
)

from app.indicators.technical import (
    add_technical_indicators,
    add_advanced_indicators,
)

from app.indicators.trend import add_trend_indicators

from app.strategies.setup_detector import detect_setup


def main():

    # --------------------------------------------------
    # 5-MINUTE DATA
    # --------------------------------------------------

    intraday_data = get_historical_data(
        DEFAULT_TICKER,
        period="5d",
        interval="5m"
    )

    intraday_data = add_technical_indicators(
        intraday_data
    )

    intraday_data = add_advanced_indicators(
        intraday_data
    )

    # --------------------------------------------------
    # DAILY DATA
    # --------------------------------------------------

    daily_data = get_daily_data(
        DEFAULT_TICKER,
        period="2y"
    )

    daily_data = add_trend_indicators(
        daily_data
    )

    # Get latest daily trend information
    daily_row = daily_data.iloc[-1]

    # --------------------------------------------------
    # LATEST INTRADAY DATA
    # --------------------------------------------------

    intraday_row = intraday_data.iloc[-1].copy()

    # Add TRUE daily SMA values to intraday row
    intraday_row["SMA_50"] = daily_row["SMA_50"]
    intraday_row["SMA_200"] = daily_row["SMA_200"]

    # --------------------------------------------------
    # SETUP ANALYSIS
    # --------------------------------------------------

    result = detect_setup(intraday_row)

    print("\n" + "=" * 70)
    print(
        f"AI-TRADER SETUP ANALYSIS: {DEFAULT_TICKER}"
    )
    print("=" * 70)

    print(
        f"Setup:              {result['setup']}"
    )

    print(
        f"Direction:          {result['direction']}"
    )

    print(
        f"Market Regime:      {result['market_regime']}"
    )

    print(
        f"Confidence:         {result['confidence']}%"
    )

    print(
        f"Bullish Evidence:   "
        f"{result['bullish_evidence']}"
    )

    print(
        f"Bearish Evidence:   "
        f"{result['bearish_evidence']}"
    )

    print("-" * 70)

    print(
        f"Daily SMA 50:       "
        f"${daily_row['SMA_50']:.2f}"
    )

    print(
        f"Daily SMA 200:      "
        f"${daily_row['SMA_200']:.2f}"
    )

    print(f"Setup Quality:      {result['quality']}")

    print("-" * 70)

    print("Reasons:")

    for reason in result["reasons"]:
        print(f"  + {reason}")

    if result["warnings"]:

        print("\nWarnings:")

        for warning in result["warnings"]:
            print(f"  ! {warning}")

    print("=" * 70)


if __name__ == "__main__":
    main()