import numpy as np
import pandas as pd


def add_advanced_indicators(data: pd.DataFrame) -> pd.DataFrame:
    """Add Stochastic, ATR, ADX and directional indicators."""
    data = data.copy()

    lowest_low = data["Low"].rolling(window=14).min()
    highest_high = data["High"].rolling(window=14).max()
    stochastic_range = (highest_high - lowest_low).replace(0, np.nan)

    data["STOCH_K"] = (
        100 * (data["Close"] - lowest_low) / stochastic_range
    )
    data["STOCH_D"] = data["STOCH_K"].rolling(window=3).mean()

    previous_close = data["Close"].shift(1)
    true_range = pd.concat(
        [
            data["High"] - data["Low"],
            (data["High"] - previous_close).abs(),
            (data["Low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    data["ATR_14"] = true_range.rolling(window=14).mean()

    high_diff = data["High"].diff()
    low_diff = -data["Low"].diff()

    plus_dm = high_diff.where(
        (high_diff > low_diff) & (high_diff > 0),
        0.0,
    )
    minus_dm = low_diff.where(
        (low_diff > high_diff) & (low_diff > 0),
        0.0,
    )

    atr = true_range.rolling(window=14).mean().replace(0, np.nan)

    plus_di = (
        100 * plus_dm.rolling(window=14).mean() / atr
    )
    minus_di = (
        100 * minus_dm.rolling(window=14).mean() / atr
    )

    data["DI_PLUS_14"] = plus_di
    data["DI_MINUS_14"] = minus_di

    di_sum = (plus_di + minus_di).replace(0, np.nan)
    dx = 100 * (plus_di - minus_di).abs() / di_sum
    data["ADX_14"] = dx.rolling(window=14).mean()

    return data


def calculate_ema(data: pd.DataFrame, period: int) -> pd.Series:
    return data["Close"].ewm(
        span=period,
        adjust=False,
    ).mean()


def calculate_vwap(data: pd.DataFrame) -> pd.Series:
    """Calculate session-based intraday VWAP."""
    result = data.copy()

    typical_price = (
        result["High"] + result["Low"] + result["Close"]
    ) / 3

    price_volume = typical_price * result["Volume"]

    cumulative_price_volume = price_volume.groupby(
        result.index.date
    ).cumsum()

    cumulative_volume = result["Volume"].groupby(
        result.index.date
    ).cumsum().replace(0, np.nan)

    return cumulative_price_volume / cumulative_volume


def add_technical_indicators(data: pd.DataFrame) -> pd.DataFrame:
    result = data.copy()

    result["EMA_9"] = calculate_ema(result, 9)
    result["EMA_20"] = calculate_ema(result, 20)
    result["EMA_50"] = calculate_ema(result, 50)
    result["VWAP"] = calculate_vwap(result)
    result["RSI_14"] = calculate_rsi(result, 14)

    macd, signal, histogram = calculate_macd(result)
    result["MACD"] = macd
    result["MACD_SIGNAL"] = signal
    result["MACD_HISTOGRAM"] = histogram
    result["RELATIVE_VOLUME"] = calculate_relative_volume(result)

    wt1, wt2 = calculate_wt_lb(result)
    result["WT_LB"] = wt1
    result["WT_LB_SIGNAL"] = wt2

    supertrend, supertrend_direction = calculate_supertrend(result)
    result["SUPERTREND"] = supertrend
    result["SUPERTREND_DIRECTION"] = supertrend_direction

    return result


def calculate_rsi(
    data: pd.DataFrame,
    period: int = 14,
) -> pd.Series:
    delta = data["Close"].diff()
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)

    average_gain = gains.ewm(
        alpha=1 / period,
        adjust=False,
    ).mean()

    average_loss = losses.ewm(
        alpha=1 / period,
        adjust=False,
    ).mean()

    relative_strength = average_gain / average_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + relative_strength))

    # Handle edge cases explicitly:
    # no losses -> RSI 100; no gains -> RSI 0; no movement -> RSI 50.
    rsi = rsi.where(average_loss != 0, 100.0)
    rsi = rsi.where(average_gain != 0, 0.0)
    rsi = rsi.where(
        ~((average_gain == 0) & (average_loss == 0)),
        50.0,
    )

    return rsi


def calculate_macd(
    data: pd.DataFrame,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
):
    ema_fast = data["Close"].ewm(
        span=fast_period,
        adjust=False,
    ).mean()

    ema_slow = data["Close"].ewm(
        span=slow_period,
        adjust=False,
    ).mean()

    macd = ema_fast - ema_slow
    signal = macd.ewm(
        span=signal_period,
        adjust=False,
    ).mean()

    return macd, signal, macd - signal



def calculate_wt_lb(
    data: pd.DataFrame,
    channel_length: int = 10,
    average_length: int = 21,
    signal_length: int = 4,
):
    """
    WaveTrend LazyBear-style oscillator (WT_LB).

    Returns:
        wt1: main WaveTrend line
        wt2: signal line (SMA of wt1)

    This is currently display/confirmation context only; it does not change
    the setup score.
    """
    ap = (
        data["High"] + data["Low"] + data["Close"]
    ) / 3.0

    esa = ap.ewm(
        span=channel_length,
        adjust=False,
    ).mean()

    deviation = (ap - esa).abs().ewm(
        span=channel_length,
        adjust=False,
    ).mean()

    safe_deviation = deviation.replace(0, np.nan)

    ci = (ap - esa) / (0.015 * safe_deviation)

    wt1 = ci.ewm(
        span=average_length,
        adjust=False,
    ).mean()

    wt2 = wt1.rolling(
        window=signal_length,
        min_periods=signal_length,
    ).mean()

    return wt1, wt2


def calculate_supertrend(
    data: pd.DataFrame,
    period: int = 10,
    multiplier: float = 3.0,
):
    """
    Standard Supertrend using Wilder-style ATR smoothing.

    Returns:
        supertrend line
        direction: 1 bullish, -1 bearish
    """
    high = data["High"].astype(float)
    low = data["Low"].astype(float)
    close = data["Close"].astype(float)

    previous_close = close.shift(1)

    true_range = pd.concat(
        [
            high - low,
            (high - previous_close).abs(),
            (low - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    atr = true_range.ewm(
        alpha=1 / period,
        adjust=False,
        min_periods=period,
    ).mean()

    hl2 = (high + low) / 2.0
    basic_upper = hl2 + multiplier * atr
    basic_lower = hl2 - multiplier * atr

    final_upper = basic_upper.copy()
    final_lower = basic_lower.copy()

    supertrend = pd.Series(
        np.nan,
        index=data.index,
        dtype="float64",
    )

    direction = pd.Series(
        0,
        index=data.index,
        dtype="int64",
    )

    for i in range(1, len(data)):
        if pd.isna(atr.iloc[i]):
            continue

        prev_upper = final_upper.iloc[i - 1]
        prev_lower = final_lower.iloc[i - 1]
        prev_close_value = close.iloc[i - 1]

        if (
            pd.isna(prev_upper)
            or basic_upper.iloc[i] < prev_upper
            or prev_close_value > prev_upper
        ):
            final_upper.iloc[i] = basic_upper.iloc[i]
        else:
            final_upper.iloc[i] = prev_upper

        if (
            pd.isna(prev_lower)
            or basic_lower.iloc[i] > prev_lower
            or prev_close_value < prev_lower
        ):
            final_lower.iloc[i] = basic_lower.iloc[i]
        else:
            final_lower.iloc[i] = prev_lower

        prev_st = supertrend.iloc[i - 1]

        if pd.isna(prev_st):
            if close.iloc[i] >= final_lower.iloc[i]:
                supertrend.iloc[i] = final_lower.iloc[i]
                direction.iloc[i] = 1
            else:
                supertrend.iloc[i] = final_upper.iloc[i]
                direction.iloc[i] = -1

        elif prev_st == prev_upper:
            if close.iloc[i] <= final_upper.iloc[i]:
                supertrend.iloc[i] = final_upper.iloc[i]
                direction.iloc[i] = -1
            else:
                supertrend.iloc[i] = final_lower.iloc[i]
                direction.iloc[i] = 1

        else:
            if close.iloc[i] >= final_lower.iloc[i]:
                supertrend.iloc[i] = final_lower.iloc[i]
                direction.iloc[i] = 1
            else:
                supertrend.iloc[i] = final_upper.iloc[i]
                direction.iloc[i] = -1

    return supertrend, direction


def calculate_relative_volume(
    data: pd.DataFrame,
    period: int = 20,
) -> pd.Series:
    """
    Relative volume against prior candles.

    Invalid/zero historical baselines remain NaN instead of being reported as
    1.0x normal volume. This prevents inf values from entering the strategy.
    """
    average_volume = (
        data["Volume"]
        .rolling(window=period)
        .mean()
        .shift(1)
        .replace(0, np.nan)
    )

    relative_volume = data["Volume"] / average_volume

    return relative_volume.replace(
        [np.inf, -np.inf],
        np.nan,
    )
