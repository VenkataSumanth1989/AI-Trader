import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import json
import math
import time

from datetime import datetime

from app.config import DEFAULT_TICKER

from app.market_data.stock_data import (
    get_historical_data,
    get_multi_timeframe_data,
    get_data_freshness,
    get_market_quote,
)

from app.indicators.technical import (
    add_technical_indicators,
    add_advanced_indicators,
)

from app.indicators.trend import (
    add_trend_indicators,
)

from app.strategies.setup_detector import (
    detect_setup,
)

from app.strategies.pullback_detector import (
    detect_pullback,
)

from app.strategies.entry_confirmation import (
    confirm_entry,
)

from app.strategies.trade_state import (
    initial_trade_state,
    update_trade_state,
)

from app.strategies.trade_plan import (
    build_trade_plan,
)

from app.strategies.setup_quality import (
    calculate_setup_quality,
)

from app.strategies.risk_manager import (
    calculate_risk_plan,
)

from app.strategies.position_sizer import (
    calculate_position_size,
)

from app.strategies.risk_guard import (
    check_risk_guard,
)

from app.strategies.decision_engine import (
    make_final_decision,
)

from app.strategies.intraday_engine import (
    calculate_intraday_signal,
)

from app.strategies.intraday_trade_plan import (
    build_intraday_trade_plan,
)

from app.indicators.price_performance import (
    calculate_price_performance,
)

from app.indicators.rsi_divergence import (
    detect_rsi_divergence,
)

from app.indicators.bollinger_bands import (
    add_bollinger_bands,
    analyze_bollinger_bands,
)

from app.indicators.obv import (
    add_obv,
    analyze_obv,
)

from app.indicators.market_structure import (
    detect_market_structure_break,
)

from app.indicators.order_blocks import (
    detect_order_block,
)

from app.indicators.support_resistance import (
    detect_support_resistance,
)


# ============================================================
# TRADINGVIEW CHART
# ============================================================

def get_tradingview_symbol(ticker_symbol: str) -> str:
    """
    Map common US tickers to their TradingView exchange symbols.

    We keep a small explicit mapping for known tickers and use
    NASDAQ as the default for other symbols.
    """
    ticker_symbol = ticker_symbol.upper().strip()

    exchange_map = {
        "DELL": "NYSE",
        "PLTR": "NASDAQ",
        "MU": "NASDAQ",
        "SNDK": "NASDAQ",
        "NVDA": "NASDAQ",
        "AMD": "NASDAQ",
        "AMZN": "NASDAQ",
        "MSFT": "NASDAQ",
        "AAPL": "NASDAQ",
        "GOOGL": "NASDAQ",
        "META": "NASDAQ",
        "TSLA": "NASDAQ",
        "AVGO": "NASDAQ",
        "NFLX": "NASDAQ",
        "INTC": "NASDAQ",
        "QCOM": "NASDAQ",
        "CSCO": "NASDAQ",
        "COST": "NASDAQ",
    }

    exchange = exchange_map.get(
        ticker_symbol,
        "NASDAQ",
    )

    return f"{exchange}:{ticker_symbol}"


def show_tradingview_chart(
    ticker_symbol: str,
    interval: str = "5",
):
    """
    Render a large TradingView Advanced Chart.
    """

    tradingview_symbol = get_tradingview_symbol(
        ticker_symbol
    )

    chart_config = {
        "autosize": True,
        "symbol": tradingview_symbol,
        "interval": interval,
        "timezone": "exchange",
        "theme": "dark",
        "style": "1",
        "locale": "en",

        # Chart controls
        "withdateranges": True,
        "hide_side_toolbar": False,
        "hide_top_toolbar": False,
        "hide_legend": False,
        "allow_symbol_change": True,
        "save_image": True,

        # Extra panels
        "details": False,
        "hotlist": False,
        "calendar": False,

        # Volume
        "studies": [
            "Volume@tv-basicstudies",
        ],

        "support_host": "https://www.tradingview.com",
    }

    config_json = json.dumps(
        chart_config
    )

    html = f"""
    <html>
    <head>
        <style>
            html,
            body {{
                margin: 0;
                padding: 0;
                width: 100%;
                height: 100%;
                overflow: hidden;
                background: #0e1117;
            }}

            .tradingview-widget-container {{
                width: 100%;
                height: 100%;
            }}

            .tradingview-widget-container__widget {{
                width: 100%;
                height: 100%;
            }}
        </style>
    </head>

    <body>

        <div class="tradingview-widget-container">

            <div
                class="tradingview-widget-container__widget"
            ></div>

            <script
                type="text/javascript"
                src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js"
                async
            >
            {config_json}
            </script>

        </div>

    </body>
    </html>
    """

    components.html(
        html,
        height=820,
        scrolling=False,
    )




# ============================================================
# DATETIME NORMALIZATION
# ============================================================

def _normalize_datetime_index_utc_naive(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize a DatetimeIndex to UTC and make it timezone-naive."""
    if frame is None or frame.empty:
        return frame
    result = frame.copy()
    if not isinstance(result.index, pd.DatetimeIndex):
        result.index = pd.to_datetime(result.index)
    idx = pd.DatetimeIndex(result.index)
    if idx.tz is not None:
        idx = idx.tz_convert("UTC").tz_localize(None)
    result.index = idx
    return result


# ============================================================
# CLOSED-CANDLE HELPER
# ============================================================

def get_last_completed_candle_index(data, interval_minutes=5):
    """
    Return the most recent completed intraday candle.

    Yahoo timestamps intraday bars at their start time. If the latest bar
    is still forming, use the previous bar for setup/entry decisions.
    """
    if data is None or data.empty:
        raise ValueError("No intraday candles available.")

    latest_index = data.index[-1]
    latest_ts = pd.Timestamp(latest_index)

    if latest_ts.tzinfo is None:
        now = pd.Timestamp.now()
    else:
        now = pd.Timestamp.now(tz=latest_ts.tz)

    completion_time = latest_ts + pd.Timedelta(minutes=interval_minutes)

    if now >= completion_time:
        return latest_index

    if len(data) < 2:
        raise ValueError("Not enough candles to identify a completed candle.")

    return data.index[-2]


# ============================================================
# ANALYSIS FUNCTION
# ============================================================

def analyze_stock(ticker_symbol):

    # --------------------------------------------------------
    # DAILY DATA
    # --------------------------------------------------------

    daily = get_historical_data(
        ticker_symbol,
        period="1y",
        interval="1d",
    )

    daily = add_trend_indicators(daily)

    daily_latest = daily.iloc[-1]

    # --------------------------------------------------------
    # INTRADAY DATA
    # --------------------------------------------------------

    data = get_historical_data(
        ticker_symbol,
        period="5d",
        interval="5m",
    )

    data_freshness = get_data_freshness(
        data,
        interval="5m",
    )

    market_quote = get_market_quote(
        ticker_symbol,
    )

    data = add_technical_indicators(data)
    data = add_advanced_indicators(data)
    data = add_bollinger_bands(data)
    data = add_obv(data)

    live_row = data.iloc[-1].copy()
    closed_candle_index = get_last_completed_candle_index(
        data,
        interval_minutes=5,
    )
    row = data.loc[closed_candle_index].copy()

    # Add daily trend indicators to both contexts.
    row["SMA_50"] = daily_latest["SMA_50"]
    row["SMA_200"] = daily_latest["SMA_200"]
    live_row["SMA_50"] = daily_latest["SMA_50"]
    live_row["SMA_200"] = daily_latest["SMA_200"]

    # --------------------------------------------------------
    # SETUP — COMPLETED 5-MINUTE CANDLE ONLY
    # --------------------------------------------------------

    setup = detect_setup(row)

    # --------------------------------------------------------
    # PULLBACK
    # --------------------------------------------------------

    pullback = detect_pullback(
        row,
        setup,
    )

    # --------------------------------------------------------
    # ENTRY CONFIRMATION
    # --------------------------------------------------------

    confirmation = confirm_entry(
        row,
        pullback,
    )

    performance_intraday = _normalize_datetime_index_utc_naive(data)
    performance_daily = _normalize_datetime_index_utc_naive(daily)

    price_performance = calculate_price_performance(
        performance_intraday,
        performance_daily,
    )

    rsi_divergence = detect_rsi_divergence(
        data,
        lookback=60,
        swing_window=3,
    )

    bollinger_analysis = analyze_bollinger_bands(
        row,
    )

    obv_analysis = analyze_obv(
        row,
    )

    return (
        ticker_symbol,
        row,
        setup,
        pullback,
        confirmation,
        data,
        price_performance,
        rsi_divergence,
        bollinger_analysis,
        obv_analysis,
        live_row,
        closed_candle_index,
        data_freshness,
        market_quote,
    )





# ============================================================
# MULTI-TIMEFRAME ANALYSIS
# ============================================================

def _timeframe_snapshot(frame):
    """
    Calculate one timeframe's technical snapshot, including
    Market Structure Break and candidate Order Block.
    """
    raw_frame = frame.copy()

    indicator_frame = add_technical_indicators(raw_frame.copy())
    indicator_frame = add_advanced_indicators(indicator_frame)
    latest = indicator_frame.iloc[-1]

    ema9 = float(latest["EMA_9"])
    ema20 = float(latest["EMA_20"])
    ema50 = float(latest["EMA_50"])
    stoch_k = float(latest["STOCH_K"])
    stoch_d = float(latest["STOCH_D"])
    macd = float(latest["MACD"])
    macd_signal = float(latest["MACD_SIGNAL"])
    adx = float(latest["ADX_14"])
    di_plus = float(latest["DI_PLUS_14"])
    di_minus = float(latest["DI_MINUS_14"])

    if ema9 > ema20 > ema50:
        trend = "BULLISH"
    elif ema9 < ema20 < ema50:
        trend = "BEARISH"
    else:
        trend = "MIXED"

    stochastic = (
        "BULLISH" if stoch_k > stoch_d
        else "BEARISH" if stoch_k < stoch_d
        else "NEUTRAL"
    )

    macd_state = (
        "BULLISH" if macd > macd_signal
        else "BEARISH" if macd < macd_signal
        else "NEUTRAL"
    )

    if adx >= 20 and di_plus > di_minus:
        direction = "BULLISH"
    elif adx >= 20 and di_minus > di_plus:
        direction = "BEARISH"
    else:
        direction = "MIXED"

    # Market structure is intentionally calculated from the raw OHLC candles.
    msb = detect_market_structure_break(
        raw_frame,
        swing_window=3,
        lookback=min(100, len(raw_frame)),
    )

    order_block = detect_order_block(
        raw_frame,
        msb,
        search_back=20,
    )

    support_resistance = detect_support_resistance(
        raw_frame,
        lookback=min(120, len(raw_frame)),
        swing_window=3,
        tolerance_percent=0.30,
    )

    zone_low = order_block.get("zone_low")
    zone_high = order_block.get("zone_high")

    if zone_low is not None and zone_high is not None:
        ob_zone = f"${zone_low:.2f} - ${zone_high:.2f}"
    else:
        ob_zone = "N/A"

    return {
        "rsi": float(latest["RSI_14"]),
        "stoch_k": stoch_k,
        "stoch_d": stoch_d,
        "stochastic": stochastic,
        "ema9": ema9,
        "ema20": ema20,
        "ema50": ema50,
        "trend": trend,
        "macd_state": macd_state,
        "adx": adx,
        "direction": direction,

        # Market structure / order block
        "msb": msb.get("msb", "NONE"),
        "msb_direction": msb.get("direction", "NEUTRAL"),
        "msb_confidence": msb.get("confidence", 0),
        "msb_break_level": msb.get("break_level"),
        "order_block": order_block.get("order_block", "NONE"),
        "ob_direction": order_block.get("direction", "NEUTRAL"),
        "ob_confidence": order_block.get("confidence", 0),
        "ob_zone": ob_zone,
        "ob_position": order_block.get("price_position", "UNKNOWN"),
        "ob_revisited": order_block.get("revisited", False),
        "ob_status": order_block.get("status", "NONE"),

        # Support / Resistance
        "support": support_resistance.get("support"),
        "resistance": support_resistance.get("resistance"),
        "sr_position": support_resistance.get("position", "UNKNOWN"),
        "breakout": support_resistance.get("breakout", "NONE"),
        "sr_confidence": support_resistance.get("confidence", 0),
        "support_touches": support_resistance.get("support_touches", 0),
        "resistance_touches": support_resistance.get("resistance_touches", 0),
    }


def calculate_multi_timeframe_analysis(ticker_symbol):
    frames = get_multi_timeframe_data(ticker_symbol)
    snapshots = {
        key: _timeframe_snapshot(frame)
        for key, frame in frames.items()
    }

    daily = frames["1d"].copy()
    daily = daily.dropna(subset=["Close", "High", "Low"])
    valid_days = len(daily)

    if valid_days == 0:
        raise ValueError(f"No valid daily history found for {ticker_symbol}")

    current = float(daily["Close"].iloc[-1])

    has_50 = valid_days >= 50
    has_200 = valid_days >= 200

    sma50 = (
        float(daily["Close"].tail(50).mean())
        if has_50 else None
    )
    sma200 = (
        float(daily["Close"].tail(200).mean())
        if has_200 else None
    )

    high50 = float(daily["High"].tail(50).max()) if has_50 else None
    low50 = float(daily["Low"].tail(50).min()) if has_50 else None
    high200 = float(daily["High"].tail(200).max()) if has_200 else None
    low200 = float(daily["Low"].tail(200).min()) if has_200 else None

    levels = {
        "current": current,
        "sma50": sma50,
        "sma200": sma200,
        "high50": high50,
        "low50": low50,
        "high200": high200,
        "low200": low200,
        "valid_days": valid_days,
        "has_50": has_50,
        "has_200": has_200,
    }

    # Never infer a 200-SMA target from missing history.
    if not has_200 or sma200 is None or not math.isfinite(sma200):
        return {
            "snapshots": snapshots,
            "levels": levels,
            "target": {
                "available": False,
                "location": "N/A",
                "distance": None,
                "percent": None,
                "score": None,
                "outlook": "NOT AVAILABLE",
                "reasons": [],
                "blockers": [
                    f"Only {valid_days} valid daily candles are available; "
                    "at least 200 are required for 200-day SMA target analysis."
                ],
            },
        }

    distance = sma200 - current
    percent = (distance / current) * 100 if current else 0.0

    if abs(distance) <= max(0.01, current * 0.001):
        target_direction = "AT_TARGET"
        location = "AT PRICE"
    elif distance > 0:
        target_direction = "UP"
        location = "ABOVE PRICE"
    else:
        target_direction = "DOWN"
        location = "BELOW PRICE"

    score = 50
    reasons = []
    blockers = []

    def supports(state):
        return (
            (target_direction == "UP" and state == "BULLISH")
            or (target_direction == "DOWN" and state == "BEARISH")
        )

    def opposes(state):
        return (
            (target_direction == "UP" and state == "BEARISH")
            or (target_direction == "DOWN" and state == "BULLISH")
        )

    if target_direction == "AT_TARGET":
        score = 100
        reasons.append("Price is already approximately at the 200-day SMA")
    else:
        checks = [
            ("4H moving-average trend", snapshots["4h"]["trend"], 15),
            ("4H Stochastic", snapshots["4h"]["stochastic"], 10),
            ("4H MACD", snapshots["4h"]["macd_state"], 10),
            ("4H ADX/DI direction", snapshots["4h"]["direction"], 10),
            ("4H Market Structure Break", snapshots["4h"]["msb_direction"], 10),
            (
                "4H Order Block direction",
                snapshots["4h"]["ob_direction"]
                if snapshots["4h"]["ob_status"] in ("ACTIVE", "RETESTED")
                else "NEUTRAL",
                5,
            ),
            ("1H trend confirmation", snapshots["1h"]["trend"], 7),
            ("Daily trend", snapshots["1d"]["trend"], 8),
        ]

        for label, state, weight in checks:
            if supports(state):
                score += weight
                reasons.append(f"{label} supports movement toward the 200-day SMA")
            elif opposes(state):
                score -= weight
                blockers.append(f"{label} opposes movement toward the 200-day SMA")

        # Order-block position is secondary context.
        # It does not predict a move by itself; it only adds/subtracts
        # a small amount when the current price location agrees with
        # the target direction.
        ob_position_4h = snapshots["4h"]["ob_position"]
        ob_status_4h = snapshots["4h"]["ob_status"]

        if ob_status_4h == "INVALIDATED":
            blockers.append(
                "The latest 4H order block has been invalidated, so it is not "
                "used as directional support"
            )

        if ob_status_4h in ("ACTIVE", "RETESTED") and target_direction == "UP":
            if ob_position_4h == "ABOVE_OB":
                score += 3
                reasons.append(
                    "Price is above the 4H bullish order-block zone"
                )
            elif ob_position_4h == "BELOW_OB":
                score -= 3
                blockers.append(
                    "Price is below the 4H order-block zone"
                )

        elif ob_status_4h in ("ACTIVE", "RETESTED") and target_direction == "DOWN":
            if ob_position_4h == "BELOW_OB":
                score += 3
                reasons.append(
                    "Price is below the 4H order-block zone"
                )
            elif ob_position_4h == "ABOVE_OB":
                score -= 3
                blockers.append(
                    "Price is above the 4H bullish order-block zone"
                )

        # 4H Support / Resistance context.
        # This is intentionally lower weight than MSB because S/R levels are
        # structural context, while a confirmed structure break is stronger evidence.
        sr4_support = snapshots["4h"]["support"]
        sr4_resistance = snapshots["4h"]["resistance"]
        sr4_breakout = snapshots["4h"]["breakout"]
        sr4_position = snapshots["4h"]["sr_position"]

        # Breakout is strong directional evidence when it points toward the target.
        if sr4_breakout == "BULLISH_BREAKOUT":
            if target_direction == "UP":
                score += 8
                reasons.append(
                    "4H bullish breakout supports movement toward the 200-day SMA"
                )
            elif target_direction == "DOWN":
                score -= 8
                blockers.append(
                    "4H bullish breakout opposes movement toward the 200-day SMA"
                )

        elif sr4_breakout == "BEARISH_BREAKDOWN":
            if target_direction == "DOWN":
                score += 8
                reasons.append(
                    "4H bearish breakdown supports movement toward the 200-day SMA"
                )
            elif target_direction == "UP":
                score -= 8
                blockers.append(
                    "4H bearish breakdown opposes movement toward the 200-day SMA"
                )

        # If still inside the range, use proximity to the relevant boundary
        # as mild context only.
        elif (
            sr4_breakout == "NONE"
            and sr4_support is not None
            and sr4_resistance is not None
        ):
            current_price_4h = levels["current"]

            if target_direction == "UP":
                distance_to_resistance = (
                    (sr4_resistance - current_price_4h) / current_price_4h * 100
                    if current_price_4h
                    else None
                )

                if (
                    distance_to_resistance is not None
                    and 0 <= distance_to_resistance <= 2
                ):
                    blockers.append(
                        "4H resistance is within 2% above current price"
                    )

            elif target_direction == "DOWN":
                distance_to_support = (
                    (current_price_4h - sr4_support) / current_price_4h * 100
                    if current_price_4h
                    else None
                )

                if (
                    distance_to_support is not None
                    and 0 <= distance_to_support <= 2
                ):
                    blockers.append(
                        "4H support is within 2% below current price"
                    )

        rsi4 = snapshots["4h"]["rsi"]
        if target_direction == "UP":
            if 50 <= rsi4 < 70:
                score += 8
                reasons.append("4H RSI supports upward momentum")
            elif rsi4 < 40:
                score -= 8
                blockers.append("4H RSI is weak for an upward target")
            elif rsi4 >= 70:
                blockers.append("4H RSI is overbought; upward move may be extended")
        else:
            if 30 < rsi4 <= 50:
                score += 8
                reasons.append("4H RSI supports downward momentum")
            elif rsi4 > 60:
                score -= 8
                blockers.append("4H RSI is strong against the downward target")
            elif rsi4 <= 30:
                blockers.append("4H RSI is oversold; downside may be extended")

        if abs(percent) > 25:
            score -= 10
            blockers.append("The 200-day SMA is more than 25% away")
        elif abs(percent) > 15:
            score -= 5
            blockers.append("The 200-day SMA is relatively far away")

    score = max(0, min(100, int(round(score))))
    outlook = (
        "AT TARGET" if target_direction == "AT_TARGET"
        else "STRONGLY SUPPORTED" if score >= 75
        else "POSSIBLE" if score >= 60
        else "MIXED" if score >= 45
        else "LOW SUPPORT"
    )

    return {
        "snapshots": snapshots,
        "levels": levels,
        "target": {
            "available": True,
            "location": location,
            "distance": distance,
            "percent": percent,
            "score": score,
            "outlook": outlook,
            "reasons": reasons,
            "blockers": blockers,
        },
    }



# ============================================================
# 1–2 DAY SWING OUTLOOK
# ============================================================

def calculate_swing_outlook(multi_timeframe, trade_state):
    """
    Create a simple 1–2 day swing bias from completed higher-timeframe candles.

    Purpose:
        - LONG  = buy first, then sell later if the move develops.
        - SHORT = short-sell first, then buy back later if the move develops.
        - WAIT  = higher timeframes are not aligned strongly enough.

    This does NOT replace the 5-minute closed-candle trade state.
    A LONG/SHORT swing bias becomes actionable only when the entry layer
    confirms with ENTRY_READY in the same direction.
    """
    snapshots = multi_timeframe["snapshots"]

    weights = [
        ("4H Direction", snapshots["4h"]["direction"], 20),
        ("Daily Direction", snapshots["1d"]["direction"], 20),
        ("4H MA Trend", snapshots["4h"]["trend"], 15),
        ("Daily MA Trend", snapshots["1d"]["trend"], 15),
        ("4H MSB", snapshots["4h"]["msb_direction"], 10),
        ("Daily MSB", snapshots["1d"]["msb_direction"], 10),
        ("1H Direction", snapshots["1h"]["direction"], 10),
    ]

    long_points = 0
    short_points = 0
    total_points = sum(weight for _, _, weight in weights)

    bullish_reasons = []
    bearish_reasons = []

    for label, state, weight in weights:
        if state == "BULLISH":
            long_points += weight
            bullish_reasons.append(label)
        elif state == "BEARISH":
            short_points += weight
            bearish_reasons.append(label)

    long_score = round((long_points / total_points) * 100)
    short_score = round((short_points / total_points) * 100)

    four_hour_direction = snapshots["4h"]["direction"]
    daily_direction = snapshots["1d"]["direction"]

    minimum_bias_score = 65
    minimum_spread = 20

    long_spread = long_score - short_score
    short_spread = short_score - long_score

    if long_score >= minimum_bias_score and long_spread >= minimum_spread:
        bias = "LONG"
        bias_score = long_score
        setup_message = (
            "Weighted higher-timeframe evidence favors a 1–2 day LONG swing."
        )
    elif short_score >= minimum_bias_score and short_spread >= minimum_spread:
        bias = "SHORT"
        bias_score = short_score
        setup_message = (
            "Weighted higher-timeframe evidence favors a 1–2 day SHORT swing."
        )
    else:
        bias = "WAIT"
        bias_score = max(long_score, short_score)
        setup_message = (
            "Higher-timeframe evidence is not strong or separated enough "
            "for a 1–2 day swing call."
        )

    trade_state_name = trade_state.get("state", "WAITING")
    entry_direction = trade_state.get("direction", "NONE")

    if (
        bias in ("LONG", "SHORT")
        and trade_state_name == "ENTRY_READY"
        and entry_direction == bias
    ):
        action = f"{bias} ENTRY READY"
    elif bias in ("LONG", "SHORT"):
        action = f"WAIT FOR {bias} ENTRY"
    else:
        action = "NO SWING ENTRY YET"

    weight_breakdown = [
        {
            "factor": label,
            "state": state,
            "weight": weight,
            "long_points": weight if state == "BULLISH" else 0,
            "short_points": weight if state == "BEARISH" else 0,
        }
        for label, state, weight in weights
    ]

    return {
        "bias": bias,
        "bias_score": bias_score,
        "long_score": long_score,
        "short_score": short_score,
        "weight_breakdown": weight_breakdown,
        "action": action,
        "message": setup_message,
        "bullish_reasons": bullish_reasons,
        "bearish_reasons": bearish_reasons,
    }


# ============================================================
# LIVE ANALYSIS + SIGNAL TRACKING
# ============================================================

def render_live_dashboard(settings: dict):
    """
    Render live stock analysis using explicit per-session settings.

    No user-specific sidebar values are stored in module globals.
    """
    current_ticker = settings["ticker"].upper().strip()
    account_size = settings["account_size"]
    risk_percent = settings["risk_percent"]
    max_position_percent = settings["max_position_percent"]
    starting_day_equity = settings["starting_day_equity"]
    daily_pnl = settings["daily_pnl"]
    consecutive_losses = settings["consecutive_losses"]
    max_daily_loss_percent = settings["max_daily_loss_percent"]
    max_consecutive_losses = settings["max_consecutive_losses"]
    auto_refresh = settings["auto_refresh"]

    if not current_ticker:
        st.warning("Enter a ticker symbol.")
        return

    # Cache the expensive market-data result per ticker for up to 5 minutes.
    # Clicking Analyze forces a fresh fetch immediately. Risk-setting changes
    # and other UI reruns reuse the same market data instead of downloading it again.
    force_refresh = bool(settings.get("force_refresh", False))
    ANALYSIS_CACHE_VERSION = "v3_datetime_intraday_plan"
    cache_bucket = st.session_state.setdefault(
        "stock_market_analysis_cache",
        {},
    )
    cached = cache_bucket.get(current_ticker)
    if cached is not None and cached.get("version") != ANALYSIS_CACHE_VERSION:
        cached = None
    now_ts = time.time()
    cache_age = (
        now_ts - cached["fetched_at"]
        if cached is not None
        else None
    )

    should_refresh = (
        force_refresh
        or cached is None
        or cache_age is None
        or cache_age >= 300
    )

    try:
        if should_refresh:
            with st.spinner(f"Refreshing market data for {current_ticker}..."):
                analysis_result = analyze_stock(current_ticker)
                multi_timeframe = calculate_multi_timeframe_analysis(
                    current_ticker
                )

            cache_bucket[current_ticker] = {
                "version": ANALYSIS_CACHE_VERSION,
                "fetched_at": time.time(),
                "analysis_result": analysis_result,
                "multi_timeframe": multi_timeframe,
            }
        else:
            analysis_result = cached["analysis_result"]
            multi_timeframe = cached["multi_timeframe"]

        (
            analyzed_ticker,
            row,
            setup,
            pullback,
            confirmation,
            data,
            price_performance,
            rsi_divergence,
            bollinger_analysis,
            obv_analysis,
            live_row,
            closed_candle_index,
            data_freshness,
            market_quote,
        ) = analysis_result

    except Exception as e:
        st.error(f"Unable to analyze {current_ticker}: {e}")
        return

    # ============================================================
    # QUALITY / RISK / FINAL DECISION
    # ============================================================

    setup_quality = calculate_setup_quality(
        row,
        setup,
    )

    risk_guard = check_risk_guard(
        account_size=float(account_size),
        starting_day_equity=float(starting_day_equity),
        daily_pnl=float(daily_pnl),
        consecutive_losses=int(consecutive_losses),
        max_daily_loss_percent=float(max_daily_loss_percent),
        max_consecutive_losses=int(max_consecutive_losses),
    )

    # Risk and position plans are generated only after an entry is confirmed.
    risk_plan = {
        "valid": False,
        "reason": "No confirmed entry",
    }

    position = {
        "valid": False,
        "reason": "No confirmed entry",
        "shares": 0,
    }

    if confirmation.get("confirmed", False):

        entry_direction = confirmation.get(
            "direction",
            "NONE",
        )

        if entry_direction in ("LONG", "SHORT"):

            risk_plan = calculate_risk_plan(
                row,
                entry_price=float(row["Close"]),
                direction=entry_direction,
            )

            if risk_plan.get("valid", False):

                position = calculate_position_size(
                    account_size=float(account_size),
                    entry_price=float(
                        risk_plan["entry_price"]
                    ),
                    stop_loss=float(
                        risk_plan["stop_loss"]
                    ),
                    risk_percent=float(risk_percent),
                    max_position_percent=float(
                        max_position_percent
                    ),
                )

    final_decision = make_final_decision(
        setup=setup,
        pullback=pullback,
        confirmation=confirmation,
        risk_plan=risk_plan,
        position=position,
        risk_guard=risk_guard,
    )


    # ========================================================
    # CLOSED-CANDLE TRADE STATE / SIGNAL PERSISTENCE
    # ========================================================

    if "trade_states" not in st.session_state:
        st.session_state["trade_states"] = {}

    previous_trade_state = st.session_state["trade_states"].get(
        analyzed_ticker,
        initial_trade_state(),
    )

    trade_state = update_trade_state(
        previous_state=previous_trade_state,
        confirmation=confirmation,
        closed_candle_time=closed_candle_index,
        keep_threshold=60,
        required_confirmations=2,
    )

    st.session_state["trade_states"][analyzed_ticker] = trade_state

    swing_outlook = calculate_swing_outlook(
        multi_timeframe=multi_timeframe,
        trade_state=trade_state,
    )

    trade_plan = build_trade_plan(
        swing_outlook=swing_outlook,
        trade_state=trade_state,
        row=row,
        multi_timeframe=multi_timeframe,
    )

    intraday_signal = calculate_intraday_signal(row)

    intraday_trade_plan = build_intraday_trade_plan(
        intraday_signal=intraday_signal,
        row=row,
        recent_data=data.loc[:closed_candle_index],
    )


    # ========================================================
    # SAVE LATEST ANALYSIS FOR CONTEXT-AWARE HELP
    # ========================================================

    st.session_state["latest_analysis"] = {
        "ticker": analyzed_ticker,
        "row": row.to_dict(),
        "setup": setup,
        "pullback": pullback,
        "confirmation": confirmation,
        "price_performance": price_performance,
        "rsi_divergence": rsi_divergence,
        "bollinger_analysis": bollinger_analysis,
        "obv_analysis": obv_analysis,
        "setup_quality": setup_quality,
        "risk_guard": risk_guard,
        "final_decision": final_decision,
        "multi_timeframe": multi_timeframe,
        "trade_state": trade_state,
        "live_price": float(live_row["Close"]),
        "closed_candle_time": str(closed_candle_index),
        "data_freshness": data_freshness,
        "market_quote": market_quote,
        "swing_outlook": swing_outlook,
        "trade_plan": trade_plan,
        "intraday_signal": intraday_signal,
        "intraday_trade_plan": intraday_trade_plan,
    }


    # ========================================================
    # SIGNAL CHANGE TRACKING
    # ========================================================

    if "signal_history" not in st.session_state:
        st.session_state["signal_history"] = {}

    ticker_history = st.session_state["signal_history"].setdefault(
        analyzed_ticker,
        [],
    )

    current_signature = (
        trade_state.get("state", "WAITING"),
        trade_state.get("direction", "NONE"),
        setup.get("setup", "NO_SETUP"),
        confirmation.get("decision", "NO_ENTRY"),
    )

    previous_signature = (
        ticker_history[-1]["signature"]
        if ticker_history
        else None
    )

    if current_signature != previous_signature:
        ticker_history.append(
            {
                "time": str(closed_candle_index),
                "price": round(float(row["Close"]), 2),
                "decision": trade_state.get("state", "WAITING"),
                "direction": setup.get("direction", "NEUTRAL"),
                "setup": setup.get("setup", "NO_SETUP"),
                "entry": confirmation.get("decision", "NO_ENTRY"),
                "confidence": final_decision.get("confidence", 0),
                "signature": current_signature,
            }
        )

        if len(ticker_history) > 50:
            del ticker_history[:-50]

    st.caption(
        f"Decision candle (closed): {closed_candle_index}  •  "
        f"Latest market candle: {data.index[-1]}  •  "
        f"Refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  •  "
        f"Auto refresh: {'ON (5 min)' if auto_refresh else 'OFF'}"
    )

    # ============================================================
    # MARKET DATA FRESHNESS
    # ============================================================

    freshness_status = data_freshness.get("status", "UNKNOWN")
    latest_market_candle = data_freshness.get("latest_candle")
    candle_age = data_freshness.get("age_minutes")
    market_session = data_freshness.get("session", "UNKNOWN")

    if freshness_status == "LIVE":
        st.caption(
            "🟢 LIVE DATA  •  "
            f"5m candle: {latest_market_candle}  •  "
            f"age {candle_age:.1f} min  •  {market_session}"
        )
    elif freshness_status == "MARKET_CLOSED":
        st.caption(
            "⚪ MARKET CLOSED  •  "
            f"latest candle: {latest_market_candle}  •  {market_session}"
        )
    else:
        st.error(
            "🔴 STALE / UNKNOWN MARKET DATA — analysis should not be trusted. "
            f"Latest candle: {latest_market_candle}"
        )

    # ============================================================
    # TOP SUMMARY
    # ============================================================

    st.divider()

    col1, col2, col3, col4 = st.columns(4)


    with col1:

        st.metric(
            "Ticker",
            analyzed_ticker,
        )


    analysis_price = float(row["Close"])
    quote_price = market_quote.get("price")
    quote_session = market_quote.get("session", "UNKNOWN")

    with col2:

        if market_quote.get("available", False) and quote_price is not None:
            quote_delta = None
            regular_close = market_quote.get("regular_close")

            if regular_close is not None and regular_close != 0:
                quote_delta = (
                    f"{quote_price - regular_close:+.2f} "
                    f"({((quote_price - regular_close) / regular_close) * 100:+.2f}%)"
                )

            st.metric(
                "Market Quote",
                f"${quote_price:.2f}",
                quote_delta,
            )
            st.caption(
                f"{quote_session} • {market_quote.get('source', 'UNKNOWN')}"
            )
        else:
            st.metric("Market Quote", "Unavailable")
            st.caption("Extended/current quote unavailable from yfinance")

    with col3:

        st.metric(
            "Analysis Price",
            f"${analysis_price:.2f}",
        )
        st.caption("Last completed 5-minute decision candle")


    with col4:

        st.metric(
            "Current Setup",
            f"{setup['direction']} • {setup['confidence']}%",
        )
        st.caption("Short-term/current indicator state — not the 1–2 day swing bias")


    if (
        market_quote.get("available", False)
        and quote_price is not None
        and analysis_price
    ):
        quote_vs_analysis_pct = (
            (quote_price - analysis_price) / analysis_price
        ) * 100

        if abs(quote_vs_analysis_pct) >= 0.50:
            st.warning(
                f"Market quote is {quote_vs_analysis_pct:+.2f}% away from the "
                "completed-candle analysis price. Trade Plan levels were calculated "
                "from the analysis candle, not from the moving extended-hours quote."
            )

    # ============================================================
    # DECISION CENTER
    # ============================================================

    st.subheader("🎯 Decision Center")

    dc1, dc2, dc3, dc4, dc5 = st.columns([1.1, 1.1, 1.2, 1.0, 1.0])

    trade_state_name = trade_state.get("state", "WAITING")
    swing_bias = swing_outlook.get("bias", "WAIT")

    with dc1:
        if swing_bias == "LONG":
            st.success("🟢 LONG BIAS")
        elif swing_bias == "SHORT":
            st.error("🔴 SHORT BIAS")
        else:
            st.info("⚪ WAIT / MIXED")
        st.caption("1–2 day bias")

    with dc2:
        if trade_state_name == "ENTRY_READY":
            st.success("🟢 ENTRY READY")
        elif trade_state_name == "CANDIDATE":
            st.warning("🟠 CANDIDATE")
        elif trade_state_name == "INVALIDATED":
            st.error("🔴 INVALIDATED")
        else:
            st.info("🟡 WAITING")
        st.caption("Closed-candle state")

    with dc3:
        st.metric("Candidate Entry", trade_state.get("direction", "NONE"))

    with dc4:
        st.metric("Entry Confidence", f"{trade_state.get('confidence', 0)}%")

    with dc5:
        st.metric(
            "Confirmations",
            f"{trade_state.get('consecutive_confirmations', 0)}/"
            f"{trade_state.get('required_confirmations', 2)}",
        )

    st.caption(
        f"{swing_outlook.get('message', '')} "
        f"Action: {swing_outlook.get('action', 'NO SWING ENTRY YET')}. "
        "Current Setup describes short-term conditions; 1–2 Day Bias describes "
        "the broader swing direction. If they disagree, WAIT for confirmation."
    )

    st.markdown("#### ⭐ Primary Indicators")

    ema_state = (
        "BULLISH"
        if row["EMA_9"] > row["EMA_20"] > row["EMA_50"]
        else "BEARISH"
        if row["EMA_9"] < row["EMA_20"] < row["EMA_50"]
        else "MIXED"
    )

    stoch_state = (
        "BULLISH"
        if row["STOCH_K"] > row["STOCH_D"]
        else "BEARISH"
        if row["STOCH_K"] < row["STOCH_D"]
        else "NEUTRAL"
    )

    wt1 = row.get("WT_LB")
    wt2 = row.get("WT_LB_SIGNAL")

    wt_state = (
        "BULLISH"
        if pd.notna(wt1) and pd.notna(wt2) and wt1 > wt2
        else "BEARISH"
        if pd.notna(wt1) and pd.notna(wt2) and wt1 < wt2
        else "NOT READY"
    )

    st_value = row.get("SUPERTREND")
    st_direction_value = row.get("SUPERTREND_DIRECTION", 0)

    supertrend_state = (
        "BULLISH"
        if st_direction_value == 1
        else "BEARISH"
        if st_direction_value == -1
        else "NOT READY"
    )

    pi1, pi2, pi3, pi4 = st.columns(4)

    with pi1:
        st.metric(
            "EMA 9 / 20 / 50",
            ema_state,
        )
        st.caption(
            f"{row['EMA_9']:.2f} / {row['EMA_20']:.2f} / {row['EMA_50']:.2f}"
        )

    with pi2:
        st.metric(
            "Stochastic",
            stoch_state,
        )
        st.caption(
            f"%K {row['STOCH_K']:.1f} • %D {row['STOCH_D']:.1f}"
        )

    with pi3:
        st.metric(
            "WT_LB",
            wt_state,
        )
        if pd.notna(wt1) and pd.notna(wt2):
            st.caption(f"WT1 {wt1:.1f} • WT2 {wt2:.1f}")
        else:
            st.caption("WaveTrend warming up")

    with pi4:
        st.metric(
            "Supertrend",
            supertrend_state,
        )
        if pd.notna(st_value):
            st.caption(f"Line ${st_value:.2f}")
        else:
            st.caption("Supertrend warming up")

    primary_states = [
        ema_state,
        stoch_state,
        wt_state,
        supertrend_state,
    ]

    bullish_primary = sum(state == "BULLISH" for state in primary_states)
    bearish_primary = sum(state == "BEARISH" for state in primary_states)

    if bullish_primary > bearish_primary:
        primary_alignment = f"BULLISH {bullish_primary}/4"
    elif bearish_primary > bullish_primary:
        primary_alignment = f"BEARISH {bearish_primary}/4"
    else:
        primary_alignment = "MIXED"

    st.caption(
        f"Primary alignment: **{primary_alignment}**. "
        "WT_LB and Supertrend are displayed as confirmation context only for now; "
        "they do not yet change the setup or swing-bias score."
    )


    st.markdown("#### ⚡ Intraday Decision Center")
    st.caption(
        "Uses the last completed 5-minute candle and is independent of the "
        "1–2 day swing bias."
    )

    intraday_direction = intraday_signal.get("direction", "WAIT")
    intraday_state = intraday_signal.get("signal", "WAIT")
    intraday_score = intraday_signal.get("confidence", 0)
    intraday_ready = intraday_signal.get("entry_ready", False)

    i1, i2, i3, i4 = st.columns(4)

    with i1:
        if intraday_direction == "LONG":
            st.success("🟢 LONG")
        elif intraday_direction == "SHORT":
            st.error("🔴 SHORT")
        else:
            st.info("⚪ WAIT")
        st.caption("Intraday direction")

    with i2:
        st.metric("Signal", intraday_state)

    with i3:
        st.metric("Intraday Score", f"{intraday_score}%")
        st.caption("Technical alignment score, not probability")

    with i4:
        st.metric(
            "Entry Readiness",
            "ALIGNED" if intraday_ready else "WAIT",
        )

    st.write(
        f"**Action:** {intraday_signal.get('action', 'WAIT — no intraday setup')}"
    )

    states = intraday_signal.get("states", {})
    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        st.metric("EMA 9/20/50", states.get("ema", "N/A"))
    with c2:
        st.metric("Supertrend", states.get("supertrend", "N/A"))
    with c3:
        st.metric("WT_LB", states.get("wt_lb", "N/A"))
    with c4:
        st.metric("Stochastic", states.get("stochastic", "N/A"))
    with c5:
        st.metric("VWAP", states.get("vwap", "N/A"))

    st.caption(
        f"Intraday score → LONG {intraday_signal.get('long_score', 0)}/100 • "
        f"SHORT {intraday_signal.get('short_score', 0)}/100 • "
        f"spread {intraday_signal.get('score_spread', 0)} points."
    )

    if (
        swing_bias in ("LONG", "SHORT")
        and intraday_direction in ("LONG", "SHORT")
        and swing_bias != intraday_direction
    ):
        st.warning(
            f"Timeframe conflict: swing bias is {swing_bias}, while intraday "
            f"direction is {intraday_direction}. Treat this as a possible "
            "counter-trend intraday move, not a change in the swing outlook."
        )

    with st.expander("Intraday reasoning", expanded=False):
        left, right = st.columns(2)

        with left:
            st.markdown("**Bullish evidence**")
            items = intraday_signal.get("bullish_reasons", [])
            if items:
                for reason in items:
                    st.write(f"✅ {reason}")
            else:
                st.write("No bullish intraday confirmations.")

        with right:
            st.markdown("**Bearish evidence**")
            items = intraday_signal.get("bearish_reasons", [])
            if items:
                for reason in items:
                    st.write(f"🔻 {reason}")
            else:
                st.write("No bearish intraday confirmations.")

        for warning in intraday_signal.get("warnings", []):
            st.warning(warning)

    st.divider()


    st.markdown("##### ⚡ Intraday Trade Plan")

    intraday_plan_status = intraday_trade_plan.get("status", "NO_SETUP")
    intraday_plan_direction = intraday_trade_plan.get("direction", "NONE")

    p1, p2, p3, p4, p5 = st.columns(5)

    with p1:
        if intraday_plan_status == "READY":
            st.success(f"🟢 READY {intraday_plan_direction}")
        elif intraday_plan_status == "WATCH":
            st.warning(f"🟠 WATCH {intraday_plan_direction}")
        elif intraday_plan_status == "EARLY":
            st.info(f"🟡 EARLY {intraday_plan_direction}")
        else:
            st.info("⚪ NO SETUP")
        st.caption("Intraday plan")

    def _fmt_intraday(value):
        return f"${value:.2f}" if value is not None else "N/A"

    with p2:
        if intraday_trade_plan.get("entry_low") is not None:
            st.metric(
                "Entry Zone",
                f"${intraday_trade_plan['entry_low']:.2f} – "
                f"${intraday_trade_plan['entry_high']:.2f}",
            )
        else:
            st.metric("Entry Zone", "N/A")

    with p3:
        st.metric(
            "Invalidation",
            _fmt_intraday(intraday_trade_plan.get("invalidation")),
        )

    with p4:
        st.metric(
            "Target 1",
            _fmt_intraday(intraday_trade_plan.get("target1")),
        )

    with p5:
        st.metric(
            "Target 2",
            _fmt_intraday(intraday_trade_plan.get("target2")),
        )

    if intraday_trade_plan.get("risk_per_share") is not None:
        st.caption(
            f"Intraday R:R → T1 1:{intraday_trade_plan.get('rr1', 0):.1f} • "
            f"T2 1:{intraday_trade_plan.get('rr2', 0):.1f} • "
            f"Risk/share ${intraday_trade_plan['risk_per_share']:.2f}"
        )

        if intraday_plan_status != "READY":
            st.caption(
                "Conditional planning levels only — WAIT/EARLY is not an entry."
            )

        if (
            swing_bias in ("LONG", "SHORT")
            and intraday_plan_direction in ("LONG", "SHORT")
            and swing_bias != intraday_plan_direction
        ):
            st.warning(
                f"Counter-trend intraday plan: swing bias is {swing_bias}, "
                f"intraday direction is {intraday_plan_direction}."
            )
    else:
        st.caption(
            intraday_trade_plan.get("reason", "No intraday plan available.")
        )

    with st.expander("Intraday trade-plan details", expanded=False):
        st.write(f"**Reason:** {intraday_trade_plan.get('reason', 'N/A')}")
        if intraday_trade_plan.get("recent_high") is not None:
            st.write(
                f"**Recent 5m High:** ${intraday_trade_plan['recent_high']:.2f}"
            )
        if intraday_trade_plan.get("recent_low") is not None:
            st.write(
                f"**Recent 5m Low:** ${intraday_trade_plan['recent_low']:.2f}"
            )
        st.caption(
            "Based on completed 5-minute data, EMA/VWAP reference, ATR, "
            "and recent 5-minute structure."
        )

    st.divider()

    st.markdown("#### 📋 Trade Plan")

    tp1, tp2, tp3, tp4, tp5 = st.columns(5)
    plan_status = trade_plan.get("status", "NO_SETUP")

    with tp1:
        if plan_status == "READY":
            st.success("🟢 READY")
        elif plan_status == "WATCH":
            st.warning("🟠 WATCH")
        elif plan_status == "RISK_TOO_WIDE":
            st.error("🔴 NO TRADE")
        elif plan_status == "INVALID":
            st.error("🔴 INVALID")
        else:
            st.info("⚪ NO SETUP")
        st.caption(
            "Risk too wide for 1–2 day plan"
            if plan_status == "RISK_TOO_WIDE"
            else "Plan status"
        )

    def _fmt_plan_price(value):
        return f"${value:.2f}" if value is not None else "N/A"

    with tp2:
        if trade_plan.get("entry_zone_low") is not None:
            st.metric(
                "Entry Zone",
                f"${trade_plan['entry_zone_low']:.2f} – "
                f"${trade_plan['entry_zone_high']:.2f}",
            )
        else:
            st.metric("Entry Zone", "N/A")

    with tp3:
        st.metric(
            "Invalidation",
            _fmt_plan_price(trade_plan.get("invalidation")),
        )

    with tp4:
        if plan_status == "RISK_TOO_WIDE":
            st.metric("Target 1", "HIDDEN")
            st.caption("No target while stop/risk is unsuitable")
        else:
            st.metric(
                "Target 1",
                _fmt_plan_price(trade_plan.get("target_1")),
            )

    with tp5:
        if plan_status == "RISK_TOO_WIDE":
            st.metric("Target 2", "HIDDEN")
            st.caption("Wait for a better entry/structure")
        else:
            st.metric(
                "Target 2",
                _fmt_plan_price(trade_plan.get("target_2")),
            )

    if trade_plan.get("risk_per_share") is not None:
        if plan_status == "RISK_TOO_WIDE":
            st.error(
                f"NO TRADE: risk/share ${trade_plan['risk_per_share']:.2f} "
                f"({trade_plan.get('risk_pct', 0):.1f}% from planned entry). "
                "The required invalidation is too far away for the configured "
                "1–2 day setup."
            )
        else:
            st.caption(
                f"R:R → T1 1:{trade_plan['risk_reward_1']:.1f}  •  "
                f"T2 1:{trade_plan['risk_reward_2']:.1f}  •  "
                f"Risk/share ${trade_plan['risk_per_share']:.2f}  •  "
                f"{trade_plan.get('trigger', '')}"
            )

        st.caption(
            f"Plan basis: completed-candle analysis price ${analysis_price:.2f}. "
            "Market Quote is display context and does not recalculate the plan "
            "until a new completed decision candle is processed."
        )
    else:
        st.caption(trade_plan.get("trigger", "No trade plan available."))

    with st.expander("Trade Plan reasoning"):
        for reason in trade_plan.get("reasons", []):
            st.write(f"✅ {reason}")
        for warning in trade_plan.get("warnings", []):
            st.warning(warning)

    with st.expander("Why this decision?"):
        left, right = st.columns(2)
        with left:
            st.markdown("**Bullish evidence**")
            items = swing_outlook.get("bullish_reasons", [])
            if items:
                for item in items:
                    st.write(f"✅ {item}")
            else:
                st.write("No strong bullish higher-timeframe evidence.")
        with right:
            st.markdown("**Bearish evidence**")
            items = swing_outlook.get("bearish_reasons", [])
            if items:
                for item in items:
                    st.write(f"⚠️ {item}")
            else:
                st.write("No strong bearish higher-timeframe evidence.")

    with st.expander("🧠 Decision Breakdown — exact scoring", expanded=False):
        st.caption(
            "This exposes the calculations already used by AI-Trader. "
            "No strategy weights are changed by this panel."
        )

        st.markdown("##### Current Setup Evidence")
        setup_total = setup.get(
            "total_evidence",
            setup.get("bullish_evidence", 0) + setup.get("bearish_evidence", 0),
        )

        a1, a2, a3, a4 = st.columns(4)
        a1.metric("Bullish Evidence", setup.get("bullish_evidence", 0))
        a2.metric("Bearish Evidence", setup.get("bearish_evidence", 0))
        a3.metric("Evidence Total", setup_total)
        a4.metric("Setup Confidence", f"{setup.get('confidence', 0)}%")

        if setup_total:
            st.caption(
                f"Raw evidence ratio: bullish {setup.get('bullish_ratio', 0):.1f}% / "
                f"bearish {setup.get('bearish_ratio', 0):.1f}%."
            )

        adjustment_rows = []
        for name, value in setup.get("confidence_adjustments", {}).items():
            if value not in (0, None):
                adjustment_rows.append({
                    "Adjustment": name.replace("_", " ").title(),
                    "Effect": value,
                })

        if adjustment_rows:
            st.dataframe(
                pd.DataFrame(adjustment_rows),
                width="stretch",
                hide_index=True,
            )

        st.markdown("##### Setup Quality Score")
        quality_rows = setup_quality.get("breakdown", [])
        if quality_rows:
            st.dataframe(
                pd.DataFrame(quality_rows).rename(
                    columns={
                        "factor": "Factor",
                        "points": "Points",
                        "detail": "Why",
                    }
                ),
                width="stretch",
                hide_index=True,
            )
            st.caption(
                f"Quality score {setup_quality.get('score', 0)}/100 "
                f"→ Grade {setup_quality.get('quality', 'N/A')}."
            )
        else:
            st.info("No setup-quality points were awarded.")

        st.markdown("##### 1–2 Day Bias Weights")
        bias_rows = swing_outlook.get("weight_breakdown", [])
        if bias_rows:
            st.dataframe(
                pd.DataFrame(bias_rows).rename(
                    columns={
                        "factor": "Factor",
                        "state": "State",
                        "weight": "Weight",
                        "long_points": "LONG",
                        "short_points": "SHORT",
                    }
                ),
                width="stretch",
                hide_index=True,
            )

        st.caption(
            f"LONG {swing_outlook.get('long_score', 0)}% vs "
            f"SHORT {swing_outlook.get('short_score', 0)}%. "
            "Bias requires >=65% plus a >=20-point advantage."
        )

        st.markdown("##### Entry Confirmation")
        e1, e2, e3, e4 = st.columns(4)
        e1.metric("Direction", confirmation.get("direction", "NONE"))
        e2.metric("Decision", confirmation.get("decision", "NO_ENTRY"))
        e3.metric(
            "Evidence",
            f"{max(confirmation.get('bullish_evidence', 0), confirmation.get('bearish_evidence', 0))}/"
            f"{confirmation.get('max_evidence', 0)}",
        )
        e4.metric("Confidence", f"{confirmation.get('confidence', 0)}%")

        st.markdown("##### Final Gate State")
        st.write(
            f"**Swing Bias:** {swing_outlook.get('bias', 'WAIT')}  •  "
            f"**Trade State:** {trade_state.get('state', 'WAITING')}  •  "
            f"**Candidate:** {trade_state.get('direction', 'NONE')}  •  "
            f"**Final Engine:** {final_decision.get('decision', 'WAIT')}"
        )
        st.caption(trade_state.get("reason", ""))

    # ============================================================
    # MAIN ANALYSIS TABS
    # ============================================================

    tab_overview, tab_chart, tab_details = st.tabs(
        ["📌 Overview", "📈 Chart & Levels", "🔬 Deep Dive"]
    )

    with tab_overview:
            # ============================================================
            # PRICE PERFORMANCE
            # ============================================================

            st.subheader("📊 Price Performance")

            p1, p2, p3, p4 = st.columns(4)

            with p1:
                st.metric(
                    "Current Price",
                    f"${price_performance['current']:.2f}",
                )

            def show_performance_metric(container, title, values):
                if values["price"] is None:
                    container.metric(title, "N/A")
                    return

                container.metric(
                    title,
                    f"${values['price']:.2f}",
                    (
                        f"{values['difference']:+.2f} "
                        f"({values['percent']:+.2f}%)"
                    ),
                )

            show_performance_metric(
                p2,
                "4 Hours Ago",
                price_performance["4h"],
            )

            show_performance_metric(
                p3,
                "1 Day Ago",
                price_performance["1d"],
            )

            show_performance_metric(
                p4,
                "1 Week Ago",
                price_performance["1w"],
            )


            # ============================================================
            # MULTI-TIMEFRAME SNAPSHOT — ALWAYS VISIBLE ABOVE CHART
            # ============================================================

            st.subheader("🧭 Multi-Timeframe Snapshot")

            snapshots = multi_timeframe["snapshots"]
            mtf_rows = []

            for label, key in [
                ("1 Hour", "1h"),
                ("4 Hour", "4h"),
                ("Daily", "1d"),
            ]:
                snap = snapshots[key]
                mtf_rows.append({
                    "TF": label,
                    "RSI 14": round(snap["rsi"], 2),
                    "Stoch %K": round(snap["stoch_k"], 2),
                    "Stoch %D": round(snap["stoch_d"], 2),
                    "Stoch": snap["stochastic"],
                    "EMA 9": round(snap["ema9"], 2),
                    "EMA 20": round(snap["ema20"], 2),
                    "EMA 50": round(snap["ema50"], 2),
                    "MA Trend": snap["trend"],
                    "MACD": snap["macd_state"],
                    "ADX": round(snap["adx"], 2),
                    "Dir": snap["direction"],
                    "MSB": snap["msb"],
                    "MSB Level": (
                        f"${snap['msb_break_level']:.2f}"
                        if snap["msb_break_level"] is not None
                        else "N/A"
                    ),
                    "MSB Conf": f"{snap['msb_confidence']}%",
                    "OB": snap["order_block"],
                    "OB Zone": snap["ob_zone"],
                    "OB Position": snap["ob_position"],
                    "OB Status": snap["ob_status"],
                    "OB Retest": "YES" if snap["ob_revisited"] else "NO",
                    "S/R": (
                        f"${snap['support']:.2f} / ${snap['resistance']:.2f}"
                        if snap["support"] is not None and snap["resistance"] is not None
                        else "N/A"
                    ),
                    "Breakout": snap["breakout"],
                })

            st.dataframe(
                pd.DataFrame(mtf_rows),
                use_container_width=True,
                hide_index=True,
            )

            st.caption(
                "Each row is calculated from that timeframe's own candles. "
                "S/R combines Support / Resistance into one compact column to keep the "
                "single-shot table readable. Breakout shows whether the latest close is "
                "still inside the range or has broken a detected level."
            )


    with tab_chart:
            st.subheader("📐 50 / 200-Day Strategic Levels")

            levels = multi_timeframe["levels"]
            l1, l2, l3, l4 = st.columns(4)

            def format_price(value):
                return f"${value:.2f}" if value is not None and math.isfinite(value) else "N/A"

            def format_range(high_value, low_value):
                if (
                    high_value is None
                    or low_value is None
                    or not math.isfinite(high_value)
                    or not math.isfinite(low_value)
                ):
                    return "N/A"
                return f"${high_value:.2f} / ${low_value:.2f}"

            with l1:
                st.metric("50-Day SMA", format_price(levels["sma50"]))
            with l2:
                st.metric("200-Day SMA", format_price(levels["sma200"]))
            with l3:
                st.metric(
                    "50-Day High / Low",
                    format_range(levels["high50"], levels["low50"]),
                )
            with l4:
                st.metric(
                    "200-Day High / Low",
                    format_range(levels["high200"], levels["low200"]),
                )

            if not levels["has_50"]:
                st.info(
                    f"Only {levels['valid_days']} valid daily candles are available. "
                    "50-day strategic levels require at least 50."
                )
            elif not levels["has_200"]:
                st.info(
                    f"Only {levels['valid_days']} valid daily candles are available. "
                    "200-day SMA/high/low require at least 200, so those values are shown as N/A."
                )

            st.subheader("🎯 4H → 200-Day SMA Target Analysis")

            target = multi_timeframe["target"]
            t1, t2, t3, t4 = st.columns(4)

            with t1:
                st.metric("Move Toward 200-Day SMA", target["outlook"])
            with t2:
                st.metric(
                    "Support Score",
                    f"{target['score']}/100" if target["score"] is not None else "N/A",
                )
            with t3:
                if target["available"]:
                    st.metric(
                        "Distance to 200 SMA",
                        f"${target['distance']:+.2f}",
                        f"{target['percent']:+.2f}%",
                    )
                else:
                    st.metric("Distance to 200 SMA", "N/A")
            with t4:
                st.metric("200-Day SMA Location", target["location"])

            st.caption(
                "200-Day SMA Location only tells you where the SMA sits relative to "
                "current price. Move Toward 200-Day SMA measures technical confluence from "
                "trend, momentum, ADX/DI, MSB, Order Block, Support/Resistance, breakout "
                "context and multiple timeframes; it is not a statistical probability or "
                "price guarantee."
            )

            if not target["available"]:
                st.warning(target["blockers"][0])
            else:
                target_left, target_right = st.columns(2)

                with target_left:
                    st.markdown("**Supporting evidence**")
                    if target["reasons"]:
                        for reason in target["reasons"]:
                            st.write(f"✅ {reason}")
                    else:
                        st.write("No strong supporting evidence.")

                with target_right:
                    st.markdown("**Opposing / caution evidence**")
                    if target["blockers"]:
                        for blocker in target["blockers"]:
                            st.write(f"⚠️ {blocker}")
                    else:
                        st.write("No major opposing evidence detected.")


            # ============================================================
            # TRADINGVIEW CHART
            # ============================================================

            st.subheader("📈 TradingView Chart")

            chart_col1, chart_col2 = st.columns([3, 1])

            with chart_col1:
                st.caption(
                    f"{analyzed_ticker} — TradingView Advanced Chart"
                )

            with chart_col2:
                chart_interval = st.selectbox(
                    "Timeframe",
                    options=[
                        ("1 minute", "1"),
                        ("5 minutes", "5"),
                        ("15 minutes", "15"),
                        ("30 minutes", "30"),
                        ("1 hour", "60"),
                        ("4 hours", "240"),
                        ("1 day", "D"),
                    ],
                    index=1,
                    format_func=lambda item: item[0],
                    key="tradingview_interval",
                )

            show_tradingview_chart(
                analyzed_ticker,
                interval=chart_interval[1],
            )


            with st.expander("🧱 Support / Resistance Details", expanded=False):

                sr_rows = []

                for label, key in [
                    ("1 Hour", "1h"),
                    ("4 Hour", "4h"),
                    ("Daily", "1d"),
                ]:
                    snap = snapshots[key]

                    sr_rows.append({
                        "Timeframe": label,
                        "Support": (
                            f"${snap['support']:.2f}"
                            if snap["support"] is not None
                            else "N/A"
                        ),
                        "Support Touches": snap["support_touches"],
                        "Resistance": (
                            f"${snap['resistance']:.2f}"
                            if snap["resistance"] is not None
                            else "N/A"
                        ),
                        "Resistance Touches": snap["resistance_touches"],
                        "Position": snap["sr_position"],
                        "Breakout": snap["breakout"],
                        "Confidence": f"{snap['sr_confidence']}%",
                    })

                st.dataframe(
                    pd.DataFrame(sr_rows),
                    use_container_width=True,
                    hide_index=True,
                )

                st.caption(
                    "Support and resistance are clustered from confirmed swing lows/highs. "
                    "Breakout requires the latest close to move beyond the detected level. "
                    "Touch count and confidence are supporting context, not probabilities."
                )



    with tab_details:
            # ============================================================
            # FINAL DECISION
            # ============================================================
            with st.expander("🎯 AI-Trader Final Decision", expanded=True):


                decision = final_decision.get(
                    "decision",
                    "WAIT",
                )

                decision_col, setup_col, risk_col = st.columns(3)

                with decision_col:

                    if decision == "BUY":
                        st.success("🟢 BUY")
                    elif decision == "SELL":
                        st.error("🔴 SELL")
                    elif decision == "NO_TRADE":
                        st.error("⛔ NO TRADE")
                    else:
                        st.warning("🟡 WAIT")

                    st.metric(
                        "Final Confidence",
                        f"{final_decision.get('confidence', 0)}%",
                    )

                with setup_col:

                    st.metric(
                        "Direction",
                        final_decision.get(
                            "direction",
                            setup["direction"],
                        ),
                    )

                    st.write(
                        f"**Market Regime:** "
                        f"{setup['market_regime']}"
                    )

                    st.write(
                        f"**Setup:** "
                        f"{setup['setup']}"
                    )

                    st.write(
                        f"**Setup Quality:** "
                        f"{setup_quality['quality']} "
                        f"({setup_quality['score']}/100)"
                    )

                with risk_col:

                    entry_confirmed = confirmation.get(
                        "confirmed",
                        False,
                    )

                    st.metric(
                        "Entry Confirmed",
                        "YES" if entry_confirmed else "NO",
                    )

                    st.write(
                        f"**Entry Decision:** "
                        f"{confirmation.get('decision', 'NO_ENTRY')}"
                    )

                    st.write(
                        f"**Risk Guard:** "
                        f"{'ALLOWED' if risk_guard.get('allowed', False) else 'BLOCKED'}"
                    )


            # ============================================================
            # RISK MANAGEMENT
            # ============================================================
            with st.expander("🛡️ Risk Management", expanded=False):


                if not confirmation.get("confirmed", False):

                    st.warning(
                        "Risk Plan: NOT GENERATED — no confirmed entry."
                    )

                    r1, r2, r3, r4 = st.columns(4)

                    with r1:
                        st.metric("Trade Status", "WAIT")

                    with r2:
                        st.metric("Position Size", "0 shares")

                    with r3:
                        st.metric(
                            "Risk Guard",
                            "ALLOWED"
                            if risk_guard.get("allowed", False)
                            else "BLOCKED",
                        )

                    with r4:
                        st.metric(
                            "Setup Quality",
                            setup_quality["quality"],
                        )

                else:

                    if risk_plan.get("valid", False):

                        r1, r2, r3, r4 = st.columns(4)

                        with r1:
                            st.metric(
                                "Entry",
                                f"${risk_plan['entry_price']:.2f}",
                            )

                        with r2:
                            st.metric(
                                "Stop Loss",
                                f"${risk_plan['stop_loss']:.2f}",
                            )

                        with r3:
                            st.metric(
                                "Target",
                                f"${risk_plan['target']:.2f}",
                            )

                        with r4:
                            st.metric(
                                "Risk / Reward",
                                f"1:{risk_plan['risk_reward']:.2f}",
                            )

                        p1, p2, p3, p4 = st.columns(4)

                        with p1:
                            st.metric(
                                "Risk / Share",
                                f"${risk_plan['risk_per_share']:.2f}",
                            )

                        with p2:
                            st.metric(
                                "Position Size",
                                (
                                    f"{position.get('shares', 0)} shares"
                                    if position.get("valid", False)
                                    else "0 shares"
                                ),
                            )

                        with p3:
                            st.metric(
                                "Position Value",
                                (
                                    f"${position.get('position_value', 0):,.2f}"
                                    if position.get("valid", False)
                                    else "$0.00"
                                ),
                            )

                        with p4:
                            st.metric(
                                "Actual Risk",
                                (
                                    f"${position.get('actual_risk', 0):,.2f}"
                                    if position.get("valid", False)
                                    else "$0.00"
                                ),
                            )

                        st.caption(
                            f"Risk plan quality: {risk_plan['quality']} | "
                            f"Account risk setting: {risk_percent:.2f}% | "
                            f"Maximum position allocation: "
                            f"{max_position_percent:.2f}%"
                        )

                    else:

                        st.error(
                            "Entry was confirmed, but a valid risk plan "
                            f"could not be generated: "
                            f"{risk_plan.get('reason', 'Unknown reason')}"
                        )


            # ============================================================
            # RISK GUARD STATUS
            # ============================================================

            with st.expander("🧯 Risk Guard Details"):

                st.write(
                    f"**Status:** "
                    f"{'ALLOWED' if risk_guard.get('allowed', False) else 'BLOCKED'}"
                )

                st.write(
                    f"**Reason:** "
                    f"{risk_guard.get('reason', 'Unknown')}"
                )

                if "daily_loss" in risk_guard:
                    st.write(
                        f"**Daily Loss:** "
                        f"${risk_guard['daily_loss']:.2f}"
                    )

                if "max_daily_loss" in risk_guard:
                    st.write(
                        f"**Maximum Daily Loss:** "
                        f"${risk_guard['max_daily_loss']:.2f}"
                    )

                if "remaining_daily_loss" in risk_guard:
                    st.write(
                        f"**Remaining Daily Risk:** "
                        f"${risk_guard['remaining_daily_loss']:.2f}"
                    )

                if "consecutive_losses" in risk_guard:
                    st.write(
                        f"**Consecutive Losses:** "
                        f"{risk_guard['consecutive_losses']}"
                    )


            # ============================================================
            # FINAL DECISION REASONS
            # ============================================================

            with st.expander("🧠 Final Decision Explanation"):

                st.markdown("### Reasons")

                reasons = final_decision.get(
                    "reasons",
                    [],
                )

                if reasons:
                    for reason in reasons:
                        st.write(f"• {reason}")
                else:
                    st.write("No decision reasons available.")

                decision_warnings = final_decision.get(
                    "warnings",
                    [],
                )

                if decision_warnings:

                    st.markdown("### Warnings")

                    for warning in decision_warnings:
                        st.write(f"⚠️ {warning}")


            # ============================================================
            # TREND
            # ============================================================
            with st.expander("📊 Trend", expanded=False):


                c1, c2, c3, c4, c5, c6 = st.columns(6)

                with c1:
                    st.metric(
                        "EMA 9",
                        f"${row['EMA_9']:.2f}",
                    )

                with c2:
                    st.metric(
                        "EMA 20",
                        f"${row['EMA_20']:.2f}",
                    )

                with c3:
                    st.metric(
                        "EMA 50",
                        f"${row['EMA_50']:.2f}",
                    )

                with c4:
                    st.metric(
                        "SMA 50",
                        f"${row['SMA_50']:.2f}",
                    )

                with c5:
                    st.metric(
                        "SMA 200",
                        f"${row['SMA_200']:.2f}",
                    )

                with c6:
                    st.metric(
                        "VWAP",
                        f"${row['VWAP']:.2f}",
                    )


            # ============================================================
            # MOMENTUM
            # ============================================================
            with st.expander("⚡ Momentum", expanded=False):


                c1, c2, c3, c4, c5 = st.columns(5)

                with c1:
                    st.metric(
                        "RSI 14",
                        f"{row['RSI_14']:.2f}",
                    )

                with c2:
                    st.metric(
                        "MACD",
                        f"{row['MACD']:.4f}",
                    )

                with c3:
                    st.metric(
                        "MACD Signal",
                        f"{row['MACD_SIGNAL']:.4f}",
                    )

                with c4:
                    st.metric(
                        "Stochastic %K",
                        f"{row['STOCH_K']:.2f}",
                    )

                with c5:
                    st.metric(
                        "Stochastic %D",
                        f"{row['STOCH_D']:.2f}",
                    )


            # ============================================================
            # BOLLINGER BANDS
            # ============================================================
            with st.expander("📏 Bollinger Bands", expanded=False):


                bb1, bb2, bb3, bb4 = st.columns(4)

                with bb1:
                    st.metric("Upper Band", f"${row['BB_UPPER']:.2f}")

                with bb2:
                    st.metric("Middle Band", f"${row['BB_MIDDLE']:.2f}")

                with bb3:
                    st.metric("Lower Band", f"${row['BB_LOWER']:.2f}")

                with bb4:
                    st.metric("%B", f"{row['BB_PERCENT_B']:.2f}")

                bb5, bb6, bb7 = st.columns(3)

                with bb5:
                    st.metric("Band Width", f"{row['BB_WIDTH']:.2f}%")

                with bb6:
                    st.metric(
                        "BB Signal",
                        bollinger_analysis.get("signal", "UNKNOWN"),
                    )

                with bb7:
                    st.metric(
                        "Price Position",
                        bollinger_analysis.get("position", "UNKNOWN"),
                    )

                for reason in bollinger_analysis.get("reasons", []):
                    st.write(f"• {reason}")

                for warning in bollinger_analysis.get("warnings", []):
                    st.warning(warning)


            # ============================================================
            # RSI DIVERGENCE
            # ============================================================
            with st.expander("🔀 RSI Divergence", expanded=False):


                d1, d2, d3 = st.columns(3)

                divergence_type = rsi_divergence.get(
                    "divergence",
                    "NONE",
                )

                divergence_direction = rsi_divergence.get(
                    "direction",
                    "NEUTRAL",
                )

                divergence_confidence = rsi_divergence.get(
                    "confidence",
                    0,
                )

                with d1:
                    st.metric(
                        "Divergence",
                        divergence_type,
                    )

                with d2:
                    st.metric(
                        "Direction",
                        divergence_direction,
                    )

                with d3:
                    st.metric(
                        "Confidence",
                        f"{divergence_confidence}%",
                    )

                price_point_1 = rsi_divergence.get("price_point_1")
                price_point_2 = rsi_divergence.get("price_point_2")
                rsi_point_1 = rsi_divergence.get("rsi_point_1")
                rsi_point_2 = rsi_divergence.get("rsi_point_2")

                if (
                    price_point_1 is not None
                    and price_point_2 is not None
                    and rsi_point_1 is not None
                    and rsi_point_2 is not None
                ):

                    dp1, dp2 = st.columns(2)

                    with dp1:
                        st.write(
                            f"**Price Swing:** "
                            f"${price_point_1:.2f} → "
                            f"${price_point_2:.2f}"
                        )

                        st.write(
                            f"**RSI Swing:** "
                            f"{rsi_point_1:.2f} → "
                            f"{rsi_point_2:.2f}"
                        )

                    with dp2:
                        if rsi_divergence.get("time_point_1") is not None:
                            st.write(
                                f"**Swing Time 1:** "
                                f"{rsi_divergence['time_point_1']}"
                            )

                        if rsi_divergence.get("time_point_2") is not None:
                            st.write(
                                f"**Swing Time 2:** "
                                f"{rsi_divergence['time_point_2']}"
                            )

                    if divergence_type == "REGULAR_BULLISH":
                        st.info(
                            "Bullish RSI divergence detected: price made a "
                            "lower swing low while RSI made a higher swing low. "
                            "This may indicate weakening downside momentum. "
                            "Entry confirmation is still required."
                        )

                    elif divergence_type == "REGULAR_BEARISH":
                        st.warning(
                            "Bearish RSI divergence detected: price made a "
                            "higher swing high while RSI made a lower swing high. "
                            "This may indicate weakening upside momentum. "
                            "Entry confirmation is still required."
                        )

                else:
                    st.info(
                        "No regular RSI divergence is currently detected."
                    )

                divergence_reasons = rsi_divergence.get(
                    "reasons",
                    [],
                )

                if divergence_reasons:
                    with st.expander("RSI Divergence Details"):
                        for reason in divergence_reasons:
                            st.write(f"• {reason}")


            # ============================================================
            # ON-BALANCE VOLUME
            # ============================================================
            with st.expander("🌊 On-Balance Volume (OBV)", expanded=False):


                o1, o2, o3, o4 = st.columns(4)

                with o1:
                    st.metric("OBV", f"{row['OBV']:,.0f}")

                with o2:
                    st.metric("OBV Signal", f"{row['OBV_SIGNAL']:,.0f}")

                with o3:
                    st.metric("OBV Change", f"{row['OBV_CHANGE']:+,.0f}")

                with o4:
                    st.metric(
                        "Volume Direction",
                        obv_analysis.get("direction", "NEUTRAL"),
                    )

                st.write(
                    f"**Signal:** {obv_analysis.get('signal', 'UNKNOWN')}  |  "
                    f"**Confidence:** {obv_analysis.get('confidence', 0)}%"
                )

                for reason in obv_analysis.get("reasons", []):
                    st.write(f"• {reason}")

                for warning in obv_analysis.get("warnings", []):
                    st.warning(warning)


            # ============================================================
            # TREND STRENGTH / VOLUME
            # ============================================================
            with st.expander("💪 Trend Strength / Volume", expanded=False):


                c1, c2, c3, c4, c5 = st.columns(5)

                with c1:
                    st.metric(
                        "ATR 14",
                        f"{row['ATR_14']:.2f}",
                    )

                with c2:
                    st.metric(
                        "ADX 14",
                        f"{row['ADX_14']:.2f}",
                    )

                with c3:
                    st.metric(
                        "DI+",
                        f"{row['DI_PLUS_14']:.2f}",
                    )

                with c4:
                    st.metric(
                        "DI-",
                        f"{row['DI_MINUS_14']:.2f}",
                    )

                with c5:
                    st.metric(
                        "Relative Volume",
                        f"{row['RELATIVE_VOLUME']:.2f}x",
                    )


            # ============================================================
            # SETUP REASONS
            # ============================================================
            with st.expander("🔎 Setup Analysis", expanded=False):


                reason_col, warning_col = st.columns(2)


                with reason_col:

                    st.markdown("### Evidence")

                    for reason in setup.get(
                        "reasons",
                        [],
                    ):

                        st.write(
                            f"✅ {reason}"
                        )


                with warning_col:

                    st.markdown("### Warnings")

                    warnings = (
                        setup.get("warnings", [])
                        + pullback.get("warnings", [])
                        + confirmation.get("warnings", [])
                    )

                    if warnings:

                        for warning in warnings:

                            st.write(
                                f"⚠️ {warning}"
                            )

                    else:

                        st.success(
                            "No major warnings"
                        )


            # ============================================================
            # PULLBACK ANALYSIS
            # ============================================================
            with st.expander("↩️ Pullback Analysis", expanded=False):


                st.write(
                    f"**Type:** {pullback['type']}"
                )

                st.write(
                    f"**Confidence:** "
                    f"{pullback['confidence']}%"
                )

                for reason in pullback.get(
                    "reasons",
                    [],
                ):

                    st.write(
                        f"• {reason}"
                    )


            # ============================================================
            # ENTRY CONFIRMATION
            # ============================================================
            with st.expander("🚦 Entry Confirmation", expanded=False):


                if confirmation["decision"] == "NO_ENTRY":

                    st.error(
                        "NO ENTRY — confirmation conditions are not satisfied."
                    )

                else:

                    st.success(
                        confirmation["decision"]
                    )

                st.write(
                    f"**Confidence:** "
                    f"{confirmation['confidence']}%"
                )

                for reason in confirmation.get(
                    "reasons",
                    [],
                ):

                    st.write(
                        f"• {reason}"
                    )



            # ========================================================
            # SIGNAL CHANGE HISTORY
            # ========================================================

            with st.expander("🕒 Signal Change History", expanded=False):

                history_rows = [
                    {
                        "Candle Time": item["time"],
                        "Price": item["price"],
                        "Decision": item["decision"],
                        "Direction": item["direction"],
                        "Setup": item["setup"],
                        "Entry": item["entry"],
                        "Confidence": item["confidence"],
                    }
                    for item in reversed(ticker_history[-10:])
                ]

                if history_rows:
                    st.dataframe(
                        pd.DataFrame(history_rows),
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    st.info("No signal changes recorded yet.")

                st.caption(
                    "A row is added only when the final decision, setup, "
                    "direction, or entry state changes."
                )


            # ============================================================
            # RAW DATA
            # ============================================================

            with st.expander(
                "📋 Show Raw Indicator Values"
            ):

                raw_values = {

                    "Price": row["Close"],

                    "Volume": row["Volume"],

                    "EMA 9": row["EMA_9"],
                    "EMA 20": row["EMA_20"],
                    "EMA 50": row["EMA_50"],

                    "SMA 50": row["SMA_50"],
                    "SMA 200": row["SMA_200"],

                    "VWAP": row["VWAP"],

                    "RSI 14": row["RSI_14"],

                    "MACD": row["MACD"],
                    "MACD Signal": row["MACD_SIGNAL"],
                    "MACD Histogram": row["MACD_HISTOGRAM"],

                    "Stochastic %K": row["STOCH_K"],
                    "Stochastic %D": row["STOCH_D"],

                    "ATR 14": row["ATR_14"],
                    "ADX 14": row["ADX_14"],

                    "DI+": row["DI_PLUS_14"],
                    "DI-": row["DI_MINUS_14"],

                    "Relative Volume": row["RELATIVE_VOLUME"],

                    "WT_LB": row.get("WT_LB"),
                    "WT_LB Signal": row.get("WT_LB_SIGNAL"),
                    "Supertrend": row.get("SUPERTREND"),
                    "Supertrend Direction": row.get("SUPERTREND_DIRECTION"),

                    "Intraday Direction": intraday_signal.get("direction"),
                    "Intraday Signal": intraday_signal.get("signal"),
                    "Intraday Score": intraday_signal.get("confidence"),
                    "Intraday Long Score": intraday_signal.get("long_score"),
                    "Intraday Short Score": intraday_signal.get("short_score"),
                    "Intraday Entry Ready": intraday_signal.get("entry_ready"),

                    "Bollinger Upper": row["BB_UPPER"],
                    "Bollinger Middle": row["BB_MIDDLE"],
                    "Bollinger Lower": row["BB_LOWER"],
                    "Bollinger Width %": row["BB_WIDTH"],
                    "Bollinger %B": row["BB_PERCENT_B"],
                    "Bollinger Signal": bollinger_analysis.get(
                        "signal",
                        "UNKNOWN",
                    ),
                    "Bollinger Position": bollinger_analysis.get(
                        "position",
                        "UNKNOWN",
                    ),

                    "OBV": row["OBV"],
                    "OBV Signal Average": row["OBV_SIGNAL"],
                    "OBV Change": row["OBV_CHANGE"],
                    "OBV Analysis": obv_analysis.get(
                        "signal",
                        "UNKNOWN",
                    ),
                    "OBV Direction": obv_analysis.get(
                        "direction",
                        "NEUTRAL",
                    ),
                    "OBV Confidence": obv_analysis.get(
                        "confidence",
                        0,
                    ),

                    "RSI Divergence": rsi_divergence.get(
                        "divergence",
                        "NONE",
                    ),
                    "RSI Divergence Direction": rsi_divergence.get(
                        "direction",
                        "NEUTRAL",
                    ),
                    "RSI Divergence Confidence": rsi_divergence.get(
                        "confidence",
                        0,
                    ),
                    "RSI Divergence Price Point 1": (
                        rsi_divergence.get("price_point_1")
                        if rsi_divergence.get("price_point_1") is not None
                        else float("nan")
                    ),
                    "RSI Divergence Price Point 2": (
                        rsi_divergence.get("price_point_2")
                        if rsi_divergence.get("price_point_2") is not None
                        else float("nan")
                    ),
                    "RSI Divergence RSI Point 1": (
                        rsi_divergence.get("rsi_point_1")
                        if rsi_divergence.get("rsi_point_1") is not None
                        else float("nan")
                    ),
                    "RSI Divergence RSI Point 2": (
                        rsi_divergence.get("rsi_point_2")
                        if rsi_divergence.get("rsi_point_2") is not None
                        else float("nan")
                    ),

                    "4 Hours Ago Price": (
                        price_performance["4h"]["price"]
                        if price_performance["4h"]["price"] is not None
                        else float("nan")
                    ),
                    "4 Hours Change %": (
                        price_performance["4h"]["percent"]
                        if price_performance["4h"]["percent"] is not None
                        else float("nan")
                    ),
                    "1 Day Ago Price": (
                        price_performance["1d"]["price"]
                        if price_performance["1d"]["price"] is not None
                        else float("nan")
                    ),
                    "1 Day Change %": (
                        price_performance["1d"]["percent"]
                        if price_performance["1d"]["percent"] is not None
                        else float("nan")
                    ),
                    "1 Week Ago Price": (
                        price_performance["1w"]["price"]
                        if price_performance["1w"]["price"] is not None
                        else float("nan")
                    ),
                    "1 Week Change %": (
                        price_performance["1w"]["percent"]
                        if price_performance["1w"]["percent"] is not None
                        else float("nan")
                    ),
                }

                st.dataframe(
                    pd.DataFrame(
                        raw_values.items(),
                        columns=[
                            "Indicator",
                            "Value",
                        ],
                    ),
                    use_container_width=True,
                    hide_index=True,
                )




def render_stock_page():
    """Render the stock-analysis page and sidebar controls."""
    st.title("📈 AI-Trader")
    st.caption(
        "Technical analysis and trade setup decision-support dashboard"
    )

    st.sidebar.header("Analysis")

    ticker = st.sidebar.text_input(
        "Ticker",
        value=DEFAULT_TICKER,
        key="stock_ticker",
    ).upper().strip()

    analyze_clicked = st.sidebar.button(
        "🔄 Analyze",
        width="stretch",
        key="stock_analyze",
        help="Force a fresh market-data download and recalculate all timeframes.",
    )

    st.sidebar.divider()
    st.sidebar.subheader("Risk Settings")

    account_size = st.sidebar.number_input(
        "Account Size ($)",
        min_value=100.0,
        value=10000.0,
        step=500.0,
        key="stock_account_size",
    )

    risk_percent = st.sidebar.number_input(
        "Risk per Trade (%)",
        min_value=0.1,
        max_value=5.0,
        value=1.0,
        step=0.1,
        key="stock_risk_percent",
    )

    max_position_percent = st.sidebar.number_input(
        "Max Position Size (%)",
        min_value=1.0,
        max_value=100.0,
        value=20.0,
        step=1.0,
        key="stock_max_position_percent",
    )

    starting_day_equity = st.sidebar.number_input(
        "Starting Day Equity ($)",
        min_value=100.0,
        value=10000.0,
        step=500.0,
        key="stock_starting_day_equity",
    )

    daily_pnl = st.sidebar.number_input(
        "Today's P/L ($)",
        value=0.0,
        step=25.0,
        key="stock_daily_pnl",
    )

    consecutive_losses = st.sidebar.number_input(
        "Consecutive Losses",
        min_value=0,
        value=0,
        step=1,
        key="stock_consecutive_losses",
    )

    max_daily_loss_percent = st.sidebar.number_input(
        "Max Daily Loss (%)",
        min_value=0.1,
        max_value=20.0,
        value=2.0,
        step=0.1,
        key="stock_max_daily_loss_percent",
    )

    max_consecutive_losses = st.sidebar.number_input(
        "Max Consecutive Losses",
        min_value=1,
        value=3,
        step=1,
        key="stock_max_consecutive_losses",
    )

    st.sidebar.divider()
    st.sidebar.subheader("Live Monitoring")

    auto_refresh = st.sidebar.toggle(
        "Auto refresh",
        value=True,
        help="Refresh AI analysis automatically every 5 minutes.",
        key="stock_auto_refresh",
    )

    if auto_refresh:
        st.sidebar.success("Live refresh: every 5 minutes")
    else:
        st.sidebar.info("Live refresh: off")

    settings = {
        "ticker": ticker,
        "account_size": float(account_size),
        "risk_percent": float(risk_percent),
        "max_position_percent": float(max_position_percent),
        "starting_day_equity": float(starting_day_equity),
        "daily_pnl": float(daily_pnl),
        "consecutive_losses": int(consecutive_losses),
        "max_daily_loss_percent": float(max_daily_loss_percent),
        "max_consecutive_losses": int(max_consecutive_losses),
        "auto_refresh": bool(auto_refresh),
        "force_refresh": bool(analyze_clicked),
    }

    refresh_rate = "300s" if auto_refresh else None

    @st.fragment(run_every=refresh_rate)
    def _render_stock_fragment():
        render_live_dashboard(settings)

    _render_stock_fragment()
