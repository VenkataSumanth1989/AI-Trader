import yfinance as yf


def get_stock_data(ticker_symbol: str):
    """
    Fetch the latest market information for a stock.
    """

    ticker = yf.Ticker(ticker_symbol)

    history = ticker.history(period="5d")

    if history.empty:
        raise ValueError(f"No market data found for {ticker_symbol}")

    latest = history.iloc[-1]
    previous = history.iloc[-2] if len(history) > 1 else None

    current_price = float(latest["Close"])

    previous_close = (
        float(previous["Close"])
        if previous is not None
        else current_price
    )

    change = current_price - previous_close
    change_percent = (change / previous_close) * 100

    return {
        "ticker": ticker_symbol.upper(),
        "price": current_price,
        "previous_close": previous_close,
        "change": change,
        "change_percent": change_percent,
        "volume": int(latest["Volume"]),
    }