from app.market_data.stock_data import get_stock_data


watchlist = ["NVDA", "PLTR", "MU", "AMD", "AAPL", "TSLA"]

for symbol in watchlist:
    try:
        stock = get_stock_data(symbol)

        print("-" * 50)
        print(f"Ticker:          {stock['ticker']}")
        print(f"Price:           ${stock['price']:.2f}")
        print(f"Previous Close:  ${stock['previous_close']:.2f}")
        print(f"Change:          ${stock['change']:.2f}")
        print(f"Change %:        {stock['change_percent']:.2f}%")
        print(f"Volume:          {stock['volume']:,}")

    except Exception as error:
        print(f"Error retrieving {symbol}: {error}")