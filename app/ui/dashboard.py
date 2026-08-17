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

from datetime import datetime

from app.config import DEFAULT_TICKER

from app.market_data.stock_data import (
    get_historical_data,
    get_multi_timeframe_data,
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
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AI-Trader",
    page_icon="📈",
    layout="wide",
)


# ============================================================
# TITLE
# ============================================================

page = st.sidebar.radio(
    "Navigation",
    ["📈 Analysis", "❓ Help / Indicator Guide"],
)

if page == "📈 Analysis":
    st.title("📈 AI-Trader")
    st.caption(
        "Technical analysis and trade setup decision-support dashboard"
    )

# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("Analysis")

ticker = st.sidebar.text_input(
    "Ticker",
    value=DEFAULT_TICKER,
).upper().strip()

analyze = st.sidebar.button(
    "🔄 Analyze",
    use_container_width=True,
)


st.sidebar.divider()
st.sidebar.subheader("Risk Settings")

account_size = st.sidebar.number_input(
    "Account Size ($)",
    min_value=100.0,
    value=10000.0,
    step=500.0,
)

risk_percent = st.sidebar.number_input(
    "Risk per Trade (%)",
    min_value=0.1,
    max_value=5.0,
    value=1.0,
    step=0.1,
)

max_position_percent = st.sidebar.number_input(
    "Max Position Size (%)",
    min_value=1.0,
    max_value=100.0,
    value=20.0,
    step=1.0,
)

starting_day_equity = st.sidebar.number_input(
    "Starting Day Equity ($)",
    min_value=100.0,
    value=10000.0,
    step=500.0,
)

daily_pnl = st.sidebar.number_input(
    "Today's P/L ($)",
    value=0.0,
    step=25.0,
)

consecutive_losses = st.sidebar.number_input(
    "Consecutive Losses",
    min_value=0,
    value=0,
    step=1,
)

max_daily_loss_percent = st.sidebar.number_input(
    "Max Daily Loss (%)",
    min_value=0.1,
    max_value=20.0,
    value=2.0,
    step=0.1,
)

max_consecutive_losses = st.sidebar.number_input(
    "Max Consecutive Losses",
    min_value=1,
    value=3,
    step=1,
)


st.sidebar.divider()
st.sidebar.subheader("Live Monitoring")

auto_refresh = st.sidebar.toggle(
    "Auto refresh",
    value=True,
    help="Refresh AI analysis automatically every 5 minutes.",
)

if auto_refresh:
    st.sidebar.success("Live refresh: every 5 minutes")
else:
    st.sidebar.info("Live refresh: off")


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

    data = add_technical_indicators(data)
    data = add_advanced_indicators(data)
    data = add_bollinger_bands(data)
    data = add_obv(data)

    row = data.iloc[-1].copy()

    # Add daily trend indicators
    row["SMA_50"] = daily_latest["SMA_50"]
    row["SMA_200"] = daily_latest["SMA_200"]

    # --------------------------------------------------------
    # SETUP
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

    price_performance = calculate_price_performance(
        data,
        daily,
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
# LIVE ANALYSIS + SIGNAL TRACKING
# ============================================================

refresh_rate = "300s" if auto_refresh else None


@st.fragment(run_every=refresh_rate)
def render_live_dashboard():

    current_ticker = ticker.upper().strip()

    if not current_ticker:
        st.warning("Enter a ticker symbol.")
        return

    try:
        with st.spinner(f"Analyzing {current_ticker}..."):
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
            ) = analyze_stock(current_ticker)

            multi_timeframe = calculate_multi_timeframe_analysis(
                current_ticker
            )

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
        final_decision.get("decision", "WAIT"),
        setup.get("setup", "NO_SETUP"),
        setup.get("direction", "NEUTRAL"),
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
                "time": str(data.index[-1]),
                "price": round(float(row["Close"]), 2),
                "decision": final_decision.get("decision", "WAIT"),
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
        f"AI candle: {data.index[-1]}  •  "
        f"Refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  •  "
        f"Auto refresh: {'ON (5 min)' if auto_refresh else 'OFF'}"
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


    with col2:

        st.metric(
            "Price",
            f"${row['Close']:.2f}",
        )


    with col3:

        st.metric(
            "Direction",
            setup["direction"],
        )


    with col4:

        st.metric(
            "Confidence",
            f"{setup['confidence']}%",
        )


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
            "Timeframe": label,
            "RSI 14": round(snap["rsi"], 2),
            "Stoch %K": round(snap["stoch_k"], 2),
            "Stoch %D": round(snap["stoch_d"], 2),
            "Stochastic": snap["stochastic"],
            "EMA 9": round(snap["ema9"], 2),
            "EMA 20": round(snap["ema20"], 2),
            "EMA 50": round(snap["ema50"], 2),
            "MA Trend": snap["trend"],
            "MACD": snap["macd_state"],
            "ADX": round(snap["adx"], 2),
            "Direction": snap["direction"],
            "MSB": snap["msb"],
            "MSB Level": (
                f"${snap['msb_break_level']:.2f}"
                if snap["msb_break_level"] is not None
                else "N/A"
            ),
            "MSB Conf": f"{snap['msb_confidence']}%",
            "Order Block": snap["order_block"],
            "OB Zone": snap["ob_zone"],
            "OB Position": snap["ob_position"],
            "OB Status": snap["ob_status"],
            "OB Revisited": "YES" if snap["ob_revisited"] else "NO",
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

if page == "📈 Analysis":
    render_live_dashboard()


# ============================================================
# HELP / INDICATOR GUIDE
# ============================================================

def render_help_page():
    st.title("❓ AI-Trader Help / Indicator Guide")
    st.caption("Plain-English explanations of the indicators and decision tools in AI-Trader.")

    st.info(
        "No single indicator is an automatic buy or sell signal. "
        "Look for agreement between trend, momentum, volume, setup, "
        "entry confirmation, and risk."
    )

    # ========================================================
    # CURRENT ANALYSIS EXPLAINED
    # ========================================================

    latest = st.session_state.get("latest_analysis")

    if latest:
        current_ticker = latest["ticker"]
        current_row = latest["row"]
        current_setup = latest["setup"]
        current_confirmation = latest["confirmation"]
        current_performance = latest["price_performance"]
        current_divergence = latest["rsi_divergence"]
        current_bollinger = latest.get("bollinger_analysis", {})
        current_obv = latest.get("obv_analysis", {})
        current_quality = latest["setup_quality"]
        current_final = latest["final_decision"]

        price = float(current_row["Close"])
        rsi = float(current_row["RSI_14"])
        macd = float(current_row["MACD"])
        macd_signal = float(current_row["MACD_SIGNAL"])
        macd_hist = float(current_row["MACD_HISTOGRAM"])
        ema9 = float(current_row["EMA_9"])
        ema20 = float(current_row["EMA_20"])
        ema50 = float(current_row["EMA_50"])
        sma50 = float(current_row["SMA_50"])
        sma200 = float(current_row["SMA_200"])
        vwap = float(current_row["VWAP"])
        adx = float(current_row["ADX_14"])
        di_plus = float(current_row["DI_PLUS_14"])
        di_minus = float(current_row["DI_MINUS_14"])
        rel_volume = float(current_row["RELATIVE_VOLUME"])
        stoch_k = float(current_row["STOCH_K"])
        stoch_d = float(current_row["STOCH_D"])
        atr = float(current_row["ATR_14"])
        bb_upper = float(current_row["BB_UPPER"])
        bb_middle = float(current_row["BB_MIDDLE"])
        bb_lower = float(current_row["BB_LOWER"])
        bb_width = float(current_row["BB_WIDTH"])
        bb_percent_b = float(current_row["BB_PERCENT_B"])
        obv = float(current_row["OBV"])
        obv_signal_value = float(current_row["OBV_SIGNAL"])
        obv_change = float(current_row["OBV_CHANGE"])

        vwap_percent = (
            ((price - vwap) / vwap) * 100
            if vwap
            else 0.0
        )

        if rsi >= 70:
            rsi_text = (
                "Overbought zone. Momentum is strong, but the stock may "
                "be extended. This is not automatically a sell signal."
            )
        elif rsi <= 30:
            rsi_text = (
                "Oversold zone. Selling has been strong and downside "
                "momentum may be stretched. This is not automatically a buy signal."
            )
        elif rsi >= 55:
            rsi_text = "Bullish momentum is currently stronger than neutral."
        elif rsi <= 45:
            rsi_text = "Bearish momentum is currently stronger than neutral."
        else:
            rsi_text = "Momentum is near the neutral zone."

        if ema9 > ema20 > ema50:
            ema_text = "EMA 9 > EMA 20 > EMA 50: short-term trend structure is bullish."
        elif ema9 < ema20 < ema50:
            ema_text = "EMA 9 < EMA 20 < EMA 50: short-term trend structure is bearish."
        else:
            ema_text = "The EMA structure is mixed; short-term trend alignment is not clean."

        if price > vwap:
            vwap_text = (
                f"Price is {abs(vwap_percent):.2f}% above VWAP, "
                "which supports intraday buyer strength."
            )
        elif price < vwap:
            vwap_text = (
                f"Price is {abs(vwap_percent):.2f}% below VWAP, "
                "which supports intraday seller strength."
            )
        else:
            vwap_text = "Price is approximately at VWAP."

        if macd > macd_signal and macd_hist > 0:
            macd_text = "MACD is above its signal with a positive histogram: bullish momentum."
        elif macd < macd_signal and macd_hist < 0:
            macd_text = "MACD is below its signal with a negative histogram: bearish momentum."
        else:
            macd_text = "MACD readings are mixed; momentum confirmation is weak."

        if adx >= 40:
            adx_strength = "strong"
        elif adx >= 25:
            adx_strength = "meaningful"
        elif adx >= 20:
            adx_strength = "developing"
        else:
            adx_strength = "weak/range-like"

        if di_plus > di_minus:
            di_text = "DI+ is above DI-, so bullish directional pressure is stronger."
        elif di_minus > di_plus:
            di_text = "DI- is above DI+, so bearish directional pressure is stronger."
        else:
            di_text = "DI+ and DI- are approximately balanced."

        if rel_volume >= 2:
            volume_text = "Very high participation compared with recent volume."
        elif rel_volume >= 1.2:
            volume_text = "Above-normal participation."
        elif rel_volume >= 0.8:
            volume_text = "Volume is around its normal range."
        else:
            volume_text = "Participation is relatively light."

        divergence_type = current_divergence.get("divergence", "NONE")
        divergence_conf = current_divergence.get("confidence", 0)

        if divergence_type == "REGULAR_BULLISH":
            divergence_text = (
                f"Regular bullish divergence ({divergence_conf}% confidence): "
                "price made a lower low while RSI made a higher low. "
                "Downside momentum may be weakening."
            )
        elif divergence_type == "REGULAR_BEARISH":
            divergence_text = (
                f"Regular bearish divergence ({divergence_conf}% confidence): "
                "price made a higher high while RSI made a lower high. "
                "Upside momentum may be weakening."
            )
        else:
            divergence_text = "No regular RSI divergence is currently detected."

        if bb_percent_b >= 1:
            bollinger_text = (
                "Price is above the upper Bollinger Band. Momentum is strong, "
                "but price may be extended above its recent range."
            )
        elif bb_percent_b >= 0.80:
            bollinger_text = (
                "Price is near the upper Bollinger Band, showing bullish pressure."
            )
        elif bb_percent_b <= 0:
            bollinger_text = (
                "Price is below the lower Bollinger Band. Selling pressure is strong, "
                "but price may be extended below its recent range."
            )
        elif bb_percent_b <= 0.20:
            bollinger_text = (
                "Price is near the lower Bollinger Band, showing bearish pressure."
            )
        elif price >= bb_middle:
            bollinger_text = (
                "Price is in the upper half of the Bollinger range."
            )
        else:
            bollinger_text = (
                "Price is in the lower half of the Bollinger range."
            )

        if bb_width < 2:
            bollinger_text += " Band width is narrow, indicating volatility compression."
        elif bb_width > 8:
            bollinger_text += " Band width is wide, indicating elevated volatility."

        obv_direction = current_obv.get("direction", "NEUTRAL")
        obv_signal_name = current_obv.get("signal", "UNKNOWN")

        if obv_direction == "BULLISH":
            obv_text = (
                "OBV is above its moving average and rising, so volume flow "
                "is confirming bullish pressure."
            )
        elif obv_direction == "BEARISH":
            obv_text = (
                "OBV is below its moving average and falling, so volume flow "
                "is confirming bearish pressure."
            )
        else:
            obv_text = (
                "OBV and its moving-average/change readings are mixed, so "
                "volume flow is not giving clear directional confirmation."
            )

        st.subheader(f"🧠 Current {current_ticker} Analysis Explained")

        x1, x2, x3, x4 = st.columns(4)

        with x1:
            st.metric("Price", f"${price:.2f}")
        with x2:
            st.metric("RSI 14", f"{rsi:.2f}")
        with x3:
            st.metric("ADX 14", f"{adx:.2f}")
        with x4:
            st.metric(
                "Final Decision",
                current_final.get("decision", "WAIT"),
            )

        st.markdown("### What the current indicators mean")

        st.write(f"**RSI:** {rsi_text}")
        st.write(f"**EMA Structure:** {ema_text}")
        st.write(f"**VWAP:** {vwap_text}")
        st.write(f"**MACD:** {macd_text}")
        st.write(
            f"**ADX / Direction:** ADX is {adx:.2f}, indicating a "
            f"{adx_strength} trend. {di_text}"
        )
        st.write(
            f"**Relative Volume:** {rel_volume:.2f}x — {volume_text}"
        )
        st.write(f"**RSI Divergence:** {divergence_text}")
        st.write(
            f"**Bollinger Bands:** {bollinger_text} "
            f"(Upper ${bb_upper:.2f}, Middle ${bb_middle:.2f}, "
            f"Lower ${bb_lower:.2f}, %B {bb_percent_b:.2f}, "
            f"Width {bb_width:.2f}%)"
        )
        st.write(
            f"**OBV:** {obv_text} "
            f"(OBV {obv:,.0f}, Signal {obv_signal_value:,.0f}, "
            f"Change {obv_change:+,.0f}, {obv_signal_name})"
        )

        current_mtf = latest.get("multi_timeframe")

        if current_mtf:
            current_target = current_mtf.get("target", {})

            st.markdown("### Move Toward 200-Day SMA")

            if current_target.get("available", False):
                target_score = current_target.get("score")
                target_outlook = current_target.get("outlook", "UNKNOWN")
                target_location = current_target.get("location", "N/A")
                target_percent = current_target.get("percent")

                st.write(
                    f"**Current assessment:** {target_outlook}  |  "
                    f"**Technical Support Score:** {target_score}/100  |  "
                    f"**200-Day SMA Location:** {target_location}"
                )

                if target_percent is not None:
                    relation = (
                        "above" if target_percent > 0
                        else "below" if target_percent < 0
                        else "at"
                    )
                    st.write(
                        f"The 200-day SMA is {abs(target_percent):.2f}% "
                        f"{relation} the current price."
                    )

                st.caption(
                    "This asks whether the current 4H setup, including trend, "
                    "momentum, MSB, Order Block, Support/Resistance and breakout "
                    "context, with 1H and Daily confirmation, supports movement "
                    "toward the 200-day SMA. The score is technical confluence, "
                    "not a probability."
                )
            else:
                st.write(
                    "**Current assessment:** NOT AVAILABLE — there is not "
                    "enough daily history for a valid 200-day SMA analysis."
                )

        st.markdown("### Current price performance")

        perf_cols = st.columns(3)
        perf_specs = [
            ("4 Hours", "4h"),
            ("1 Day", "1d"),
            ("1 Week", "1w"),
        ]

        for container, (label, key) in zip(perf_cols, perf_specs):
            perf = current_performance.get(key, {})
            percent = perf.get("percent")
            ref_price = perf.get("price")

            with container:
                if percent is None or ref_price is None:
                    st.metric(label, "N/A")
                else:
                    st.metric(
                        label,
                        f"{percent:+.2f}%",
                        f"Ref ${ref_price:.2f}",
                    )

        bullish_points = []
        bearish_points = []
        caution_points = []

        if ema9 > ema20 > ema50:
            bullish_points.append("bullish EMA alignment")
        elif ema9 < ema20 < ema50:
            bearish_points.append("bearish EMA alignment")

        if price > vwap:
            bullish_points.append("price above VWAP")
        elif price < vwap:
            bearish_points.append("price below VWAP")

        if macd > macd_signal and macd_hist > 0:
            bullish_points.append("bullish MACD")
        elif macd < macd_signal and macd_hist < 0:
            bearish_points.append("bearish MACD")

        if adx >= 25 and di_plus > di_minus:
            bullish_points.append("ADX confirms bullish directional pressure")
        elif adx >= 25 and di_minus > di_plus:
            bearish_points.append("ADX confirms bearish directional pressure")

        if rsi >= 70:
            caution_points.append("RSI is overbought")
        elif rsi <= 30:
            caution_points.append("RSI is oversold")

        if stoch_k >= 80 and stoch_d >= 80:
            caution_points.append("Stochastic is overbought")
        elif stoch_k <= 20 and stoch_d <= 20:
            caution_points.append("Stochastic is oversold")

        if atr > 0 and abs(price - vwap) > (2 * atr):
            caution_points.append("price is more than 2 ATR from VWAP")

        if divergence_type == "REGULAR_BULLISH":
            bullish_points.append("bullish RSI divergence")
        elif divergence_type == "REGULAR_BEARISH":
            bearish_points.append("bearish RSI divergence")

        bb_signal = current_bollinger.get("signal", "UNKNOWN")
        if bb_signal in ("BULLISH_PRESSURE", "MILD_BULLISH"):
            bullish_points.append("Bollinger Bands show bullish pressure")
        elif bb_signal in ("BEARISH_PRESSURE", "MILD_BEARISH"):
            bearish_points.append("Bollinger Bands show bearish pressure")
        elif bb_signal == "STRONG_UPPER_EXTENSION":
            caution_points.append("price is above the upper Bollinger Band")
        elif bb_signal == "STRONG_LOWER_EXTENSION":
            caution_points.append("price is below the lower Bollinger Band")

        if bb_width < 2:
            caution_points.append("Bollinger Band volatility is compressed")
        elif bb_width > 8:
            caution_points.append("Bollinger Band volatility is elevated")

        if obv_direction == "BULLISH":
            bullish_points.append("OBV confirms bullish volume flow")
        elif obv_direction == "BEARISH":
            bearish_points.append("OBV confirms bearish volume flow")

        st.markdown("### What this means now")

        st.write(
            f"**Market Regime:** {current_setup.get('market_regime', 'UNKNOWN')}  |  "
            f"**Direction:** {current_setup.get('direction', 'NEUTRAL')}  |  "
            f"**Setup:** {current_setup.get('setup', 'NO_SETUP')}  |  "
            f"**Setup Quality:** {current_quality.get('quality', 'UNKNOWN')} "
            f"({current_quality.get('score', 0)}/100)"
        )

        if bullish_points:
            st.success(
                "Bullish evidence: " + "; ".join(bullish_points) + "."
            )

        if bearish_points:
            st.error(
                "Bearish evidence: " + "; ".join(bearish_points) + "."
            )

        if caution_points:
            st.warning(
                "Caution: " + "; ".join(caution_points) + "."
            )

        if current_confirmation.get("confirmed", False):
            st.info(
                "The strategy currently has an entry confirmation. "
                "Review the Analysis page's risk plan before considering a trade."
            )
        else:
            st.info(
                "The strategy does not currently have a confirmed entry. "
                "The indicator readings above are context, not an instruction to trade."
            )

        st.divider()

    else:
        st.warning(
            "No analyzed ticker is available yet. Go to the Analysis page, "
            "analyze a ticker, then return here to see a plain-English "
            "explanation of its current readings."
        )

    st.subheader("🧭 How to Read AI-Trader")
    st.markdown("""
1. **Market Regime** — Understand the broader trend.
2. **Direction & Setup** — See what direction the current evidence favors.
3. **Trend** — Review EMA, SMA and VWAP.
4. **Momentum** — Review RSI, MACD and Stochastic.
5. **RSI Divergence** — Check whether price and momentum disagree.
6. **Strength & Volume** — Review ADX, DI+/DI- and Relative Volume.
7. **Pullback & Entry Confirmation** — Decide whether the setup is ready.
8. **Final Decision** — Review BUY, SELL, WAIT or NO TRADE and its reasons.
9. **Risk Management** — Review stop, target, position size and Risk Guard.
""")

    st.subheader("📊 Price Performance")
    with st.expander("Current Price vs 4 Hours / 1 Day / 1 Week"):
        st.write("Shows how far today's current price is from earlier reference prices.")
        st.markdown("""
- **Positive %:** current price is higher.
- **Negative %:** current price is lower.
- **Dollar difference:** actual price movement.
- **Percentage difference:** makes moves easier to compare between stocks.
""")

    st.subheader("📈 Trend Indicators")
    with st.expander("EMA 9 / EMA 20 / EMA 50"):
        st.write("EMA is a moving average that reacts more quickly to recent prices.")
        st.markdown("""
- **EMA 9:** very short-term trend.
- **EMA 20:** short-term trend.
- **EMA 50:** intermediate trend.
- **EMA 9 > EMA 20 > EMA 50:** strong bullish alignment.
- **EMA 9 < EMA 20 < EMA 50:** strong bearish alignment.
""")

    with st.expander("SMA 50 / SMA 200"):
        st.write("SMA is the average closing price over a fixed number of periods.")
        st.markdown("""
- **SMA 50:** medium-term trend.
- **SMA 200:** long-term trend.
- Price above SMA 200 generally supports stronger long-term structure.
- SMA 50 above SMA 200 is generally bullish; below it is generally bearish.
""")

    with st.expander("VWAP — Volume Weighted Average Price"):
        st.write("VWAP is an average price weighted by trading volume.")
        st.markdown("""
- Price **above VWAP:** buyers may have more intraday control.
- Price **below VWAP:** sellers may have more intraday control.
- VWAP can act like dynamic support or resistance.
- A price far from VWAP may be extended, making it risky to chase.
""")

    st.subheader("⚡ Momentum Indicators")
    with st.expander("RSI 14 — Relative Strength Index"):
        st.write("RSI measures momentum from 0 to 100.")
        st.markdown("""
- **Above 70:** commonly considered overbought.
- **Below 30:** commonly considered oversold.
- **Above 50:** generally stronger bullish momentum.
- **Below 50:** generally weaker/bearish momentum.

Overbought does not automatically mean SELL, and oversold does not automatically mean BUY.
""")

    with st.expander("MACD / Signal / Histogram"):
        st.write("MACD compares faster and slower moving averages to measure momentum.")
        st.markdown("""
- **MACD above Signal:** bullish momentum indication.
- **MACD below Signal:** bearish momentum indication.
- **Positive Histogram:** MACD is above its signal.
- **Negative Histogram:** MACD is below its signal.
- A growing histogram can indicate strengthening momentum.
""")

    with st.expander("Stochastic %K / %D"):
        st.write("Stochastic compares the latest price with its recent trading range.")
        st.markdown("""
- **Above 80:** commonly considered overbought.
- **Below 20:** commonly considered oversold.
- **%K above/crossing %D:** can support bullish momentum.
- **%K below/crossing %D:** can support bearish momentum.
""")

    with st.expander("Bollinger Bands"):
        st.write(
            "Bollinger Bands show where price sits relative to its recent "
            "average and volatility range."
        )
        st.markdown("""
- **Middle Band:** 20-period moving average.
- **Upper Band:** middle band plus two standard deviations.
- **Lower Band:** middle band minus two standard deviations.
- **%B near 1.0:** price is near the upper band.
- **%B near 0.0:** price is near the lower band.
- **Narrow Band Width:** volatility is compressed.
- **Wide Band Width:** volatility is elevated.

Touching an upper band does not automatically mean SELL, and touching a lower
band does not automatically mean BUY. In a strong trend, price can remain near
one band for an extended period.
""")

    with st.expander("RSI Divergence"):
        st.write("Divergence means price and RSI are moving differently.")
        st.markdown("""
**Regular Bullish Divergence**
- Price makes a **lower low**.
- RSI makes a **higher low**.
- Selling momentum may be weakening.

**Regular Bearish Divergence**
- Price makes a **higher high**.
- RSI makes a **lower high**.
- Buying momentum may be weakening.

AI-Trader currently treats divergence as supporting information, not a standalone trade signal.
""")

    st.subheader("💪 Strength, Volatility & Volume")
    with st.expander("ATR 14 — Average True Range"):
        st.write("ATR measures volatility, not direction.")
        st.markdown("""
- Higher ATR = larger normal price swings.
- Lower ATR = quieter price action.
- AI-Trader can use ATR when calculating stop-loss and target distances.
""")

    with st.expander("ADX 14 — Average Directional Index"):
        st.write("ADX measures trend strength, but not whether the trend is up or down.")
        st.markdown("""
- **Below 20:** weak/range-like trend.
- **20–25:** trend may be developing.
- **Above 25:** meaningful trend strength.
- **Above 40:** strong trend.
""")

    with st.expander("DI+ / DI-"):
        st.markdown("""
- **DI+ above DI-:** bullish directional pressure is stronger.
- **DI- above DI+:** bearish directional pressure is stronger.
- Combine them with ADX to judge both direction and strength.
""")

    with st.expander("Relative Volume"):
        st.write("Relative Volume compares current activity with normal/recent volume.")
        st.markdown("""
- **1.0x:** roughly normal volume.
- **Above 1.0x:** more activity than normal.
- **2.0x:** roughly twice the comparison volume.
- Strong moves with high relative volume generally have more participation.
""")

    with st.expander("OBV — On-Balance Volume"):
        st.write(
            "OBV tracks whether trading volume is generally flowing with "
            "up-closes or down-closes."
        )
        st.markdown("""
- When price closes higher, that period's volume is added to OBV.
- When price closes lower, that period's volume is subtracted.
- **OBV above its moving average and rising:** bullish volume confirmation.
- **OBV below its moving average and falling:** bearish volume confirmation.
- **Mixed OBV:** volume flow does not clearly confirm direction.

The absolute OBV number is less important than its direction and relationship
to its recent moving average. AI-Trader uses OBV as supporting evidence rather
than as a standalone BUY or SELL signal.
""")

    st.subheader("🧱 Support / Resistance & Breakouts")

    with st.expander("Support / Resistance"):
        st.markdown("""
- **Support:** a price area built from clustered confirmed swing lows.
- **Resistance:** a price area built from clustered confirmed swing highs.
- The compact **S/R** column shows `Support / Resistance` in one place.
- **INSIDE_RANGE:** current price is between detected support and resistance.
- **ABOVE_RESISTANCE:** current price is above detected resistance.
- **BELOW_SUPPORT:** current price is below detected support.
- **Touch count:** how many confirmed swing points contributed to the level.
- **Confidence:** a rule-based structural score based mainly on repeated touches and breakout context; it is not a probability.
""")

    with st.expander("Breakout / Breakdown"):
        st.markdown("""
- **BULLISH_BREAKOUT:** the latest close is above detected resistance.
- **BEARISH_BREAKDOWN:** the latest close is below detected support.
- **NONE:** price remains inside the detected support/resistance range.

AI-Trader requires a **close** beyond the level rather than only a wick through it.
The detector is currently display-only and does not yet change BUY/SELL decisions.
""")

    st.subheader("🏗️ Market Structure / Order Blocks")

    with st.expander("MSB — Market Structure Break"):
        st.markdown("""
- **BULLISH_MSB:** price closed above a previously confirmed swing high.
- **BEARISH_MSB:** price closed below a previously confirmed swing low.
- **MSB Level:** the exact prior swing high/low that price broke to create the MSB.
- **NONE:** no confirmed break was found in the current lookback window.
- The displayed confidence describes the strength of the detected break under AI-Trader's current rules; it is not a probability of future price movement.

AI-Trader calculates MSB separately for the **1 Hour, 4 Hour and Daily** candles.
""")

    with st.expander("Order Block (OB)"):
        st.markdown("""
After a confirmed MSB, AI-Trader identifies a **candidate order block**:

- After a **bullish MSB**, the last bearish candle before the break is treated as a candidate **BULLISH_OB**.
- After a **bearish MSB**, the last bullish candle before the break is treated as a candidate **BEARISH_OB**.
- **OB Zone** shows that candle's High-to-Low price range.
- **ABOVE_OB:** current price is above the zone.
- **BELOW_OB:** current price is below the zone.
- **INSIDE_OB:** current price is currently trading inside the zone.
- **OB Revisited = YES:** price has traded back into that zone after the structure break.
- **ACTIVE:** the zone has not yet been revisited or invalidated.
- **RETESTED:** price revisited the zone, but the zone still remains valid.
- **INVALIDATED:** a bullish OB later closed below its zone low, or a bearish OB later closed above its zone high.

Invalidated order blocks are no longer allowed to contribute directional support to the 200-day SMA confluence score.

This is a rule-based candidate order block, not proof of institutional buying or selling. We will add stronger filters later if testing shows they are useful.
""")

    st.subheader("🧭 Multi-Timeframe & Strategic Levels")

    with st.expander("Move Toward 200-Day SMA / Technical Support Score"):
        st.write(
            "This asks whether the current technical setup supports movement "
            "toward the 200-day simple moving average (SMA), mainly using the "
            "4-hour chart with 1-hour and Daily confirmation."
        )
        st.markdown("""
- **STRONGLY SUPPORTED:** most technical evidence supports movement toward the 200-day SMA.
- **POSSIBLE:** reasonable support exists, but confirmation is not as strong.
- **MIXED:** supporting and opposing evidence conflict.
- **LOW SUPPORT:** current technical evidence mostly does not support movement toward the 200-day SMA.
- **AT TARGET:** price is already approximately at the 200-day SMA.
- **NOT AVAILABLE:** insufficient daily history to calculate a valid 200-day SMA.

**Technical Support Score**
- Combines 4H MA trend, RSI, Stochastic, MACD, ADX/DI, **4H MSB, 4H Order Block direction/position, 4H Support/Resistance and confirmed breakout/breakdown**, 1H confirmation, Daily trend and target distance.
- A confirmed 4H breakout/breakdown has more weight than simple proximity to support or resistance.
- 4H MSB still carries more weight than OB position because a confirmed structure break is stronger evidence than location relative to a candidate order block.
- It is a **confluence score, not a probability**. A score of 75/100 does not mean a 75% chance of reaching the SMA.

**200-Day SMA Location**
- **ABOVE PRICE:** the SMA is above current price.
- **BELOW PRICE:** the SMA is below current price.
- **AT PRICE:** current price is approximately at the SMA.

Location describes where the SMA is; it is not itself a prediction.
""")

    with st.expander("50 / 200-Day Strategic Levels"):
        st.markdown("""
- **50-Day SMA:** average closing price over the latest 50 valid daily candles.
- **200-Day SMA:** average closing price over the latest 200 valid daily candles.
- **50-Day High / Low:** highest high and lowest low over the latest 50 valid daily candles.
- **200-Day High / Low:** highest high and lowest low over the latest 200 valid daily candles.
- AI-Trader displays **N/A** when enough history is not available.
""")

    st.subheader("🎯 AI-Trader Decision Terms")
    with st.expander("Market Regime"):
        st.markdown("""
- **BULLISH:** broader structure favors upward trends.
- **BEARISH:** broader structure favors downward trends.
- **NEUTRAL:** longer-term evidence is mixed.

A bearish setup inside a bullish regime is a counter-trend setup and deserves extra caution.
""")

    with st.expander("Direction / Setup / Setup Quality"):
        st.markdown("""
- **Direction:** bullish, bearish or neutral bias.
- **Setup:** the trading context detected by AI-Trader.
- **Setup Quality:** how well the evidence supports that setup.
- A good setup still needs entry confirmation and acceptable risk.
""")

    with st.expander("Pullback Analysis"):
        st.write(
            "A pullback is a temporary move against a larger trend. "
            "AI-Trader checks whether weakness/strength looks like a pullback "
            "or possible reversal risk."
        )

    with st.expander("Entry Confirmation"):
        st.write("Entry Confirmation is the gate between finding a setup and considering a trade.")
        st.markdown("""
- **NO_ENTRY:** confirmation conditions are not satisfied.
- A bullish or bearish setup can still produce **WAIT**.
- This helps avoid trading from one indicator alone.
""")

    with st.expander("BUY / SELL / WAIT / NO TRADE"):
        st.markdown("""
- **BUY:** long-entry conditions are confirmed.
- **SELL:** bearish/short-entry conditions are confirmed.
- **WAIT:** the setup is not sufficiently confirmed.
- **NO TRADE:** strategy or risk conditions block the trade.
""")

    st.subheader("🛡️ Risk Management")
    with st.expander("Stop Loss / Target / Risk-Reward"):
        st.markdown("""
- **Entry:** planned entry price.
- **Stop Loss:** exit level if the trade moves against the plan.
- **Target:** planned profit-taking level.
- **Risk / Share:** distance between entry and stop.
- **Risk / Reward:** potential loss compared with potential gain.

Example: **1:2** means the planned reward is twice the amount being risked.
""")

    with st.expander("Position Size"):
        st.write(
            "Position sizing calculates how many shares fit within your "
            "risk-per-trade and maximum-position limits. A wider stop usually "
            "means fewer shares."
        )

    with st.expander("Risk Guard"):
        st.write(
            "Risk Guard can block another trade when daily-loss or "
            "consecutive-loss limits have been reached."
        )

    st.subheader("⚠️ Important Reminder")
    st.warning(
        "Technical indicators can produce false signals. AI-Trader is a "
        "decision-support tool, not a guarantee. Also consider news, earnings, "
        "market conditions, liquidity and your own risk limits."
    )


if page == "❓ Help / Indicator Guide":
    render_help_page()