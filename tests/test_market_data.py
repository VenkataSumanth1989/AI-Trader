from app.config import DEFAULT_TICKER
from app.market_data.stock_data import get_stock_data


stock = get_stock_data(DEFAULT_TICKER)

print("Ticker:", stock["ticker"])
print("Price:", stock["price"])
print("Previous Close:", stock["previous_close"])
print("Change:", stock["change"])
print("Change %:", stock["change_percent"])
print("Volume:", stock["volume"])