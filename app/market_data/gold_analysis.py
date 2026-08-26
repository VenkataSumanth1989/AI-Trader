import pandas as pd
import numpy as np

from app.market_data.gold_data import get_xauusd_candles
from app.indicators.market_structure import detect_market_structure_break
from app.indicators.order_blocks import detect_order_block
from app.indicators.support_resistance import detect_support_resistance


def _rma(series, period=14):
    """
    Wilder-style moving average.

    Seed with the first period SMA, then apply Wilder's recursive update.
    This makes RSI/ATR/ADX behavior closer to standard charting conventions.
    """
    values = series.astype(float).copy()
    result = pd.Series(np.nan, index=values.index, dtype="float64")

    valid = values.dropna()
    if len(valid) < period:
        return result

    seed_index = valid.index[period - 1]
    seed = valid.iloc[:period].mean()
    result.loc[seed_index] = seed

    start_pos = values.index.get_loc(seed_index)

    previous = seed
    for i in range(start_pos + 1, len(values)):
        current = values.iloc[i]

        if pd.isna(current):
            result.iloc[i] = previous
            continue

        previous = ((previous * (period - 1)) + current) / period
        result.iloc[i] = previous

    return result


def _rsi(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = _rma(gain, period)
    avg_loss = _rma(loss, period)
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return (100 - (100 / (1 + rs))).fillna(50.0)


def _atr(df, period=14):
    prev_close = df["Close"].shift(1)
    tr = pd.concat(
        [
            df["High"] - df["Low"],
            (df["High"] - prev_close).abs(),
            (df["Low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return _rma(tr, period)


def _adx(df, period=14):
    high = df["High"]
    low = df["Low"]

    up_move = high.diff()
    down_move = -low.diff()

    plus_dm = pd.Series(
        np.where((up_move > down_move) & (up_move > 0), up_move, 0.0),
        index=df.index,
    )
    minus_dm = pd.Series(
        np.where((down_move > up_move) & (down_move > 0), down_move, 0.0),
        index=df.index,
    )

    atr = _atr(df, period).replace(0, np.nan)

    plus_di = 100 * (
        _rma(plus_dm, period) / atr
    )
    minus_di = 100 * (
        _rma(minus_dm, period) / atr
    )

    dx = (
        100
        * (plus_di - minus_di).abs()
        / (plus_di + minus_di).replace(0, np.nan)
    )
    adx = _rma(dx, period)

    return adx.fillna(0.0), plus_di.fillna(0.0), minus_di.fillna(0.0)


def add_gold_indicators(df):
    out = df.copy()
    close = out["Close"]

    out["EMA_9"] = close.ewm(span=9, adjust=False).mean()
    out["EMA_20"] = close.ewm(span=20, adjust=False).mean()
    out["EMA_50"] = close.ewm(span=50, adjust=False).mean()

    out["RSI_14"] = _rsi(close, 14)

    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    out["MACD"] = ema12 - ema26
    out["MACD_SIGNAL"] = out["MACD"].ewm(span=9, adjust=False).mean()

    low14 = out["Low"].rolling(14).min()
    high14 = out["High"].rolling(14).max()
    denom = (high14 - low14).replace(0, np.nan)

    out["STOCH_K"] = (100 * (close - low14) / denom).fillna(50.0)
    out["STOCH_D"] = out["STOCH_K"].rolling(3).mean().fillna(50.0)

    out["ATR_14"] = _atr(out, 14)

    adx, di_plus, di_minus = _adx(out, 14)
    out["ADX_14"] = adx
    out["DI_PLUS_14"] = di_plus
    out["DI_MINUS_14"] = di_minus

    return out


def _snapshot(raw):
    frame = add_gold_indicators(raw.copy())
    latest = frame.iloc[-1]

    ema9 = float(latest["EMA_9"])
    ema20 = float(latest["EMA_20"])
    ema50 = float(latest["EMA_50"])

    if ema9 > ema20 > ema50:
        trend = "BULLISH"
    elif ema9 < ema20 < ema50:
        trend = "BEARISH"
    else:
        trend = "MIXED"

    stoch_state = (
        "BULLISH"
        if latest["STOCH_K"] > latest["STOCH_D"]
        else "BEARISH"
        if latest["STOCH_K"] < latest["STOCH_D"]
        else "NEUTRAL"
    )

    macd_state = (
        "BULLISH"
        if latest["MACD"] > latest["MACD_SIGNAL"]
        else "BEARISH"
        if latest["MACD"] < latest["MACD_SIGNAL"]
        else "NEUTRAL"
    )

    adx = float(latest["ADX_14"])
    di_plus = float(latest["DI_PLUS_14"])
    di_minus = float(latest["DI_MINUS_14"])

    if adx >= 20 and di_plus > di_minus:
        direction = "BULLISH"
    elif adx >= 20 and di_minus > di_plus:
        direction = "BEARISH"
    else:
        direction = "MIXED"

    msb = detect_market_structure_break(
        raw,
        swing_window=3,
        lookback=min(100, len(raw)),
    )

    ob = detect_order_block(
        raw,
        msb,
        search_back=20,
    )

    sr = detect_support_resistance(
        raw,
        lookback=min(120, len(raw)),
        swing_window=3,
        tolerance_percent=0.20,
    )

    return {
        "price": float(latest["Close"]),
        "rsi": float(latest["RSI_14"]),
        "stoch_k": float(latest["STOCH_K"]),
        "stoch_d": float(latest["STOCH_D"]),
        "stochastic": stoch_state,
        "ema9": ema9,
        "ema20": ema20,
        "ema50": ema50,
        "trend": trend,
        "macd": macd_state,
        "adx": adx,
        "di_plus": di_plus,
        "di_minus": di_minus,
        "direction": direction,
        "atr": float(latest["ATR_14"]),
        "msb": msb.get("msb", "NONE"),
        "msb_direction": msb.get("direction", "NEUTRAL"),
        "msb_level": msb.get("break_level"),
        "order_block": ob.get("order_block", "NONE"),
        "ob_direction": ob.get("direction", "NEUTRAL"),
        "ob_status": ob.get("status", "NONE"),
        "support": sr.get("support"),
        "resistance": sr.get("resistance"),
        "breakout": sr.get("breakout", "NONE"),
        "latest_time": str(frame.index[-1]),
    }


def calculate_gold_analysis():
    frames = {
        "5m": get_xauusd_candles("5min", 160),
        "1h": get_xauusd_candles("1h", 160),
        "4h": get_xauusd_candles("4h", 160),
        "1d": get_xauusd_candles("1day", 250),
    }

    snapshots = {
        key: _snapshot(frame)
        for key, frame in frames.items()
    }

    weights = [
        ("4H direction", snapshots["4h"]["direction"], 25),
        ("Daily direction", snapshots["1d"]["direction"], 25),
        ("4H EMA trend", snapshots["4h"]["trend"], 15),
        ("Daily EMA trend", snapshots["1d"]["trend"], 15),
        ("4H MSB", snapshots["4h"]["msb_direction"], 10),
        ("1H direction", snapshots["1h"]["direction"], 10),
    ]

    long_points = 0
    short_points = 0
    total = sum(weight for _, _, weight in weights)

    bullish_reasons = []
    bearish_reasons = []

    for label, state, weight in weights:
        if state == "BULLISH":
            long_points += weight
            bullish_reasons.append(label)
        elif state == "BEARISH":
            short_points += weight
            bearish_reasons.append(label)

    long_score = round(long_points / total * 100)
    short_score = round(short_points / total * 100)

    if long_score >= 65 and long_score - short_score >= 20:
        bias = "LONG"
        alignment = long_score
    elif short_score >= 65 and short_score - long_score >= 20:
        bias = "SHORT"
        alignment = short_score
    else:
        bias = "WAIT"
        alignment = max(long_score, short_score)

    return {
        "frames": frames,
        "snapshots": snapshots,
        "bias": bias,
        "alignment": alignment,
        "long_score": long_score,
        "short_score": short_score,
        "bullish_reasons": bullish_reasons,
        "bearish_reasons": bearish_reasons,
        "quote": snapshots["5m"]["price"],
        "quote_time": snapshots["5m"]["latest_time"],
    }
