from app.config import DEFAULT_TICKER
from app.market_data.stock_data import get_historical_data
from app.indicators.technical import add_technical_indicators
from app.indicators.technical import (
    add_technical_indicators,
    add_advanced_indicators,
)
from app.indicators.trend import add_trend_indicators
from app.strategies.setup_detector import detect_setup
from app.strategies.setup_quality import calculate_setup_quality


def main():
    ticker = DEFAULT_TICKER

    print("\n" + "=" * 70)
    print(f"AI-TRADER SETUP QUALITY: {ticker}")
    print("=" * 70)

    # Daily data for long-term trend
    daily_data = get_historical_data(
        ticker,
        period="1y",
        interval="1d"
    )

    daily_data = add_trend_indicators(daily_data)

    # Intraday data
    intraday_data = get_historical_data(
        ticker,
        period="5d",
        interval="5m"
    )

    intraday_data = add_technical_indicators(intraday_data)
    intraday_data = add_advanced_indicators(intraday_data)

    latest = intraday_data.iloc[-1]

    # Add latest daily trend values
    latest = latest.copy()

    latest["SMA_50"] = daily_data["SMA_50"].iloc[-1]
    latest["SMA_200"] = daily_data["SMA_200"].iloc[-1]

    # Detect setup
    setup = detect_setup(latest)

    # Evaluate setup quality
    quality = calculate_setup_quality(
        latest,
        setup
    )

    print(f"Setup:              {setup['setup']}")
    print(f"Direction:          {setup['direction']}")
    print(f"Market Regime:      {setup['market_regime']}")
    print("-" * 70)

    print(f"Quality Score:      {quality['score']}/100")
    print(f"Setup Quality:      {quality['quality']}")
    print(f"Decision:           {quality['decision']}")

    print("-" * 70)

    print("Positive Factors:")

    for reason in quality["reasons"]:
        print(f"  + {reason}")

    if quality["warnings"]:
        print("\nWarnings:")

        for warning in quality["warnings"]:
            print(f"  ! {warning}")

    print("=" * 70)


if __name__ == "__main__":
    main()