from app.config import DEFAULT_TICKER
from app.market_data.stock_data import get_historical_data
from app.indicators.technical import (
    add_technical_indicators,
    add_advanced_indicators,
)
from app.indicators.trend import add_trend_indicators
from app.strategies.setup_detector import detect_setup
from app.strategies.pullback_detector import detect_pullback


def main():

    ticker = DEFAULT_TICKER

    print("\n" + "=" * 70)
    print(f"AI-TRADER PULLBACK ANALYSIS: {ticker}")
    print("=" * 70)

    # --------------------------------------------------
    # DAILY TREND DATA
    # --------------------------------------------------

    daily = get_historical_data(
        ticker,
        period="1y",
        interval="1d"
    )

    daily = add_trend_indicators(daily)

    # --------------------------------------------------
    # INTRADAY DATA
    # --------------------------------------------------

    intraday = get_historical_data(
        ticker,
        period="5d",
        interval="5m"
    )

    intraday = add_technical_indicators(intraday)
    intraday = add_advanced_indicators(intraday)

    latest = intraday.iloc[-1].copy()

    # Add long-term trend values
    latest["SMA_50"] = daily["SMA_50"].iloc[-1]
    latest["SMA_200"] = daily["SMA_200"].iloc[-1]

    # --------------------------------------------------
    # SETUP
    # --------------------------------------------------

    setup = detect_setup(latest)

    # --------------------------------------------------
    # PULLBACK
    # --------------------------------------------------

    pullback = detect_pullback(
        latest,
        setup
    )

    print(f"Direction:          {setup['direction']}")
    print(f"Market Regime:      {setup['market_regime']}")
    print("-" * 70)

    print(f"Pullback:           {pullback['pullback']}")
    print(f"Type:               {pullback['type']}")
    print(f"Confidence:         {pullback['confidence']}%")
    print(f"Bullish Evidence:   {pullback['bullish_evidence']}")
    print(f"Bearish Evidence:   {pullback['bearish_evidence']}")

    print("-" * 70)

    if pullback["reasons"]:

        print("Reasons:")

        for reason in pullback["reasons"]:
            print(f"  + {reason}")

    if pullback["warnings"]:

        print("\nWarnings:")

        for warning in pullback["warnings"]:
            print(f"  ! {warning}")

    print("=" * 70)


if __name__ == "__main__":
    main()