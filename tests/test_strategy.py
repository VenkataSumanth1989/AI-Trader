from app.config import DEFAULT_TICKER
from app.market_data.stock_data import get_historical_data
from app.indicators.technical import add_technical_indicators
from app.strategies.momentum_strategy import calculate_signal


data = get_historical_data(
    DEFAULT_TICKER,
    period="5d",
    interval="5m"
)

data = add_technical_indicators(data)

latest = data.iloc[-1]

result = calculate_signal(latest)

print("\n" + "=" * 60)
print(f"AI-TRADER STRATEGY ANALYSIS: {DEFAULT_TICKER}")
print("=" * 60)

print(f"Price:       ${latest['Close']:.2f}")
print(f"VWAP:        ${latest['VWAP']:.2f}")
print(f"RSI:         {latest['RSI_14']:.2f}")
print(f"MACD:        {latest['MACD']:.4f}")
print(f"Rel Volume:  {latest['RELATIVE_VOLUME']:.2f}x")

print("-" * 60)

print(f"Score:       {result['score']}/100")
print(f"Signal:      {result['signal']}")

print("\nReasons:")

for reason in result["reasons"]:
    print(f"  ✓ {reason}")

print("=" * 60)