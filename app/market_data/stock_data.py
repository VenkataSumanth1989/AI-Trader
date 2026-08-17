import yfinance as yf
import pandas as pd


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

def get_multi_timeframe_data(ticker_symbol: str):
    """Fetch independent 1H, 4H and daily OHLCV datasets."""
    ticker = yf.Ticker(ticker_symbol)

    hourly = ticker.history(period="60d", interval="1h")
    daily = ticker.history(period="2y", interval="1d")

    if hourly.empty:
        raise ValueError(f"No hourly market data found for {ticker_symbol}")
    if daily.empty:
        raise ValueError(f"No daily market data found for {ticker_symbol}")

    hourly = hourly[["Open", "High", "Low", "Close", "Volume"]].dropna(
        subset=["Open", "High", "Low", "Close"]
    )

    # Build 4-hour bars inside each trading day so an overnight gap is
    # never accidentally included in one 4-hour candle.
    bars = []
    for _, session in hourly.groupby(hourly.index.date):
        session = session.sort_index()
        for start in range(0, len(session), 4):
            block = session.iloc[start:start + 4]
            if block.empty:
                continue
            bars.append({
                "Date": block.index[-1],
                "Open": block["Open"].iloc[0],
                "High": block["High"].max(),
                "Low": block["Low"].min(),
                "Close": block["Close"].iloc[-1],
                "Volume": block["Volume"].sum(),
            })

    four_hour = pd.DataFrame(bars)
    if four_hour.empty:
        raise ValueError(f"No 4-hour market data found for {ticker_symbol}")

    four_hour = four_hour.set_index("Date")

    return {
        "1h": hourly,
        "4h": four_hour,
        "1d": daily,
    }