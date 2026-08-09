from app.config import DEFAULT_TICKER
from app.market_data.stock_data import get_historical_data

data = get_historical_data(
    DEFAULT_TICKER,
    period="5d",
    interval="5m"
)

print(f"\n{DEFAULT_TICKER} Historical Data")
print("=" * 80)

print(data.tail(10))

print("\nNumber of rows:", len(data))
print("Columns:", list(data.columns))