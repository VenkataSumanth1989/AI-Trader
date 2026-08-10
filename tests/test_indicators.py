from app.config import DEFAULT_TICKER
from app.market_data.stock_data import get_historical_data
from app.indicators.technical import add_technical_indicators


data = get_historical_data(
    DEFAULT_TICKER,
    period="5d",
    interval="5m"
)

data = add_technical_indicators(data)

print(f"\n{DEFAULT_TICKER} Technical Indicators")
print("=" * 100)

latest = data.tail(10)

for timestamp, row in latest.iterrows():
    print("\n" + "=" * 80)
    print(f"Time: {timestamp}")
    print(f"Close:            {row['Close']:.2f}")
    print(f"Volume:           {row['Volume']:,.0f}")
    print(f"EMA 9:            {row['EMA_9']:.2f}")
    print(f"EMA 20:           {row['EMA_20']:.2f}")
    print(f"EMA 50:           {row['EMA_50']:.2f}")
    print(f"VWAP:             {row['VWAP']:.2f}")
    print(f"RSI 14:           {row['RSI_14']:.2f}")
    print(f"MACD:             {row['MACD']:.4f}")
    print(f"MACD Signal:      {row['MACD_SIGNAL']:.4f}")
    print(f"MACD Histogram:   {row['MACD_HISTOGRAM']:.4f}")
    print(f"Relative Volume:  {row['RELATIVE_VOLUME']:.2f}x")