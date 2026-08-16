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
def get_historical_data(
    ticker_symbol: str,
    period: str = "1mo",
    interval: str = "1d"
):
    """
    Fetch historical OHLCV data for a stock.
    """

    ticker = yf.Ticker(ticker_symbol)

    history = ticker.history(
        period=period,
        interval=interval
    )

    if history.empty:
        raise ValueError(f"No historical data found for {ticker_symbol}")

    return history
def get_daily_data(ticker_symbol: str, period: str = "2y"):
    """
    Fetch daily OHLCV data for long-term trend analysis.

    Used for:
        - SMA 50
        - SMA 200
        - Long-term market regime
    """

    ticker = yf.Ticker(ticker_symbol)

    history = ticker.history(
        period=period,
        interval="1d"
    )

    if history.empty:
        raise ValueError(
            f"No daily market data found for {ticker_symbol}"
        )

    return history