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

print(
    data[
        [
            "Close",
            "Volume",
            "EMA_9",
            "EMA_20",
            "EMA_50",
            "VWAP"
        ]
    ].tail(10)
)