from app.config import DEFAULT_TICKER
from app.market_data.stock_data import get_historical_data
from app.indicators.trend import (
    add_trend_indicators,
    determine_market_regime,
)


data = get_historical_data(
    DEFAULT_TICKER,
    period="2y",
    interval="1d"
)

data = add_trend_indicators(data)

latest = data.iloc[-1]

regime = determine_market_regime(latest)

print("\n" + "=" * 60)
print(f"LONG-TERM TREND ANALYSIS: {DEFAULT_TICKER}")
print("=" * 60)

print(f"Price:       ${latest['Close']:.2f}")
print(f"SMA 50:      ${latest['SMA_50']:.2f}")
print(f"SMA 200:     ${latest['SMA_200']:.2f}")
print(f"Regime:      {regime}")

print("=" * 60)