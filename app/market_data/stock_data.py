import time
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import yfinance as yf


INTRADAY_INTERVALS = {
    "1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h"
}


def _normalize_history(history):
    if history is None or history.empty:
        return pd.DataFrame()

    history = history.copy()

    if isinstance(history.columns, pd.MultiIndex):
        level0 = history.columns.get_level_values(0)
        level1 = history.columns.get_level_values(-1)

        if "Close" in level0:
            history.columns = level0
        elif "Close" in level1:
            history.columns = level1

    required = ["Open", "High", "Low", "Close", "Volume"]

    if not {"Open", "High", "Low", "Close"}.issubset(history.columns):
        return pd.DataFrame()

    available = [c for c in required if c in history.columns]

    return history[available].dropna(
        subset=["Open", "High", "Low", "Close"]
    )


def _latest_timestamp(history):
    if history is None or history.empty:
        return None

    ts = pd.Timestamp(history.index[-1])

    if ts.tzinfo is None:
        ts = ts.tz_localize("America/New_York")
    else:
        ts = ts.tz_convert("America/New_York")

    return ts


def _market_session_state():
    now_et = datetime.now(ZoneInfo("America/New_York"))

    if now_et.weekday() >= 5:
        return "CLOSED"

    minutes = now_et.hour * 60 + now_et.minute

    if minutes < (9 * 60 + 30):
        return "PREMARKET"

    if minutes <= 16 * 60:
        return "REGULAR"

    return "AFTERHOURS"


def _max_allowed_age_minutes(interval):
    return {
        "1m": 6,
        "2m": 8,
        "5m": 12,
        "15m": 25,
        "30m": 45,
        "60m": 80,
        "1h": 80,
        "90m": 115,
    }.get(interval, 20)


def get_data_freshness(history, interval="5m"):
    """
    Return freshness information for the supplied market data.
    """

    latest = _latest_timestamp(history)
    session = _market_session_state()

    result = {
        "status": "UNKNOWN",
        "session": session,
        "latest_candle": latest,
        "age_minutes": None,
        "max_age_minutes": _max_allowed_age_minutes(interval),
        "reason": "",
    }

    if latest is None:
        result["status"] = "STALE"
        result["reason"] = "No latest candle timestamp is available."
        return result

    now_et = pd.Timestamp.now(tz="America/New_York")
    age_minutes = (now_et - latest).total_seconds() / 60.0
    result["age_minutes"] = age_minutes

    if session == "REGULAR":
        if age_minutes > result["max_age_minutes"]:
            result["status"] = "STALE"
            result["reason"] = (
                f"Latest {interval} candle is {age_minutes:.1f} minutes old "
                "during regular market hours."
            )
        else:
            result["status"] = "LIVE"
            result["reason"] = (
                f"Latest {interval} candle is within the freshness window."
            )
    else:
        result["status"] = "MARKET_CLOSED"
        result["reason"] = (
            "US regular market is not currently open, so the latest completed "
            "market candle may be from the prior session."
        )

    return result


def _fetch_history_once(ticker_symbol, period, interval):
    """
    Try both yfinance access paths and keep the one with the newest candle.
    """

    candidates = []

    try:
        ticker = yf.Ticker(ticker_symbol)
        history = ticker.history(
            period=period,
            interval=interval,
            auto_adjust=False,
            actions=False,
            prepost=False,
            repair=True,
        )
        history = _normalize_history(history)

        if not history.empty:
            candidates.append(history)
    except Exception:
        pass

    try:
        history = yf.download(
            ticker_symbol,
            period=period,
            interval=interval,
            auto_adjust=False,
            actions=False,
            prepost=False,
            repair=True,
            progress=False,
            threads=False,
        )
        history = _normalize_history(history)

        if not history.empty:
            candidates.append(history)
    except Exception:
        pass

    if not candidates:
        return pd.DataFrame()

    candidates.sort(
        key=lambda frame: _latest_timestamp(frame),
        reverse=True,
    )

    return candidates[0]


def get_historical_data(
    ticker_symbol: str,
    period: str = "1mo",
    interval: str = "1d",
    retries: int = 2,
):
    """
    Fetch OHLCV data.

    During regular US market hours, intraday data must be fresh.
    Stale data is retried and ultimately rejected rather than silently used.
    """

    attempts = max(1, retries + 1)
    freshest = pd.DataFrame()

    for attempt in range(attempts):
        history = _fetch_history_once(
            ticker_symbol,
            period,
            interval,
        )

        if not history.empty:
            if freshest.empty:
                freshest = history
            else:
                old_ts = _latest_timestamp(freshest)
                new_ts = _latest_timestamp(history)

                if old_ts is None or (new_ts is not None and new_ts > old_ts):
                    freshest = history

            freshness = get_data_freshness(history, interval)

            if freshness["status"] != "STALE":
                return history

        if attempt < attempts - 1:
            time.sleep(1.0)

    if freshest.empty:
        raise ValueError(
            f"No historical data found for {ticker_symbol}"
        )

    freshness = get_data_freshness(freshest, interval)

    if interval in INTRADAY_INTERVALS and freshness["status"] == "STALE":
        latest = freshness["latest_candle"]
        age = freshness["age_minutes"]

        raise ValueError(
            f"STALE MARKET DATA for {ticker_symbol}: latest {interval} "
            f"candle is {latest} ({age:.1f} minutes old). Yahoo Finance did "
            "not return fresh intraday data after retries. AI-Trader stopped "
            "instead of calculating indicators from an old price."
        )

    return freshest


def get_stock_data(ticker_symbol: str):
    history = get_historical_data(
        ticker_symbol,
        period="5d",
        interval="1d",
    )

    latest = history.iloc[-1]
    previous = history.iloc[-2] if len(history) > 1 else None

    current_price = float(latest["Close"])
    previous_close = (
        float(previous["Close"])
        if previous is not None
        else current_price
    )

    change = current_price - previous_close
    change_percent = (
        (change / previous_close) * 100
        if previous_close
        else 0.0
    )

    return {
        "ticker": ticker_symbol.upper(),
        "price": current_price,
        "previous_close": previous_close,
        "change": change,
        "change_percent": change_percent,
        "volume": int(latest["Volume"]),
    }


def get_daily_data(
    ticker_symbol: str,
    period: str = "2y",
):
    return get_historical_data(
        ticker_symbol,
        period=period,
        interval="1d",
    )


def get_multi_timeframe_data(ticker_symbol: str):
    """
    Fetch 1H and daily data and construct approximate 4H candles
    from the 1H bars within each trading day.
    """

    hourly = get_historical_data(
        ticker_symbol,
        period="60d",
        interval="1h",
    )

    daily = get_historical_data(
        ticker_symbol,
        period="2y",
        interval="1d",
    )

    hourly = hourly[
        ["Open", "High", "Low", "Close", "Volume"]
    ].dropna(
        subset=["Open", "High", "Low", "Close"]
    )

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
        raise ValueError(
            f"No 4-hour market data found for {ticker_symbol}"
        )

    four_hour = four_hour.set_index("Date")

    return {
        "1h": hourly,
        "4h": four_hour,
        "1d": daily,
    }