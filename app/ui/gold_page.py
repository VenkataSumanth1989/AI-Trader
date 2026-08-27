import json
import time
import streamlit as st
import streamlit.components.v1 as components

from app.market_data.gold_analysis import calculate_gold_analysis
from app.strategies.gold_decision import calculate_gold_decision


def render_gold_page():
        st.title("🥇 Gold — XAUUSD")
        st.caption(
            "Spot-gold technical analysis and 1–2 day trade decision-support workspace."
        )

        g1, g2, g3, g4 = st.columns([1, 1, 1, 0.8])

        with g1:
            st.metric("Asset", "Gold Spot")

        with g2:
            st.metric("Symbol", "XAUUSD")

        with g3:
            st.metric("AI Analysis", "ACTIVE")

        with g4:
            refresh_gold = st.button(
                "🔄 Refresh Gold",
                use_container_width=True,
                key="gold_refresh_button",
            )

        st.caption(
            "Gold analysis uses XAU/USD spot data from Twelve Data, while the chart "
            "uses OANDA:XAUUSD on TradingView. We intentionally do not substitute "
            "GC=F futures for spot-gold calculations."
        )

        st.subheader("🧭 Gold Decision Center")

        # Keep the expensive 5m/1H/4H/Daily API result in this browser session.
        # A manual refresh always bypasses the cache. Otherwise the cached result
        # is reused for up to 5 minutes so chart/timeframe UI changes stay fast.
        cache_key = "gold_analysis_cache"
        now_ts = time.time()
        cached = st.session_state.get(cache_key)
        cache_age = (
            now_ts - cached["fetched_at"]
            if cached is not None
            else None
        )

        should_refresh = (
            refresh_gold
            or cached is None
            or cache_age is None
            or cache_age >= 300
        )

        try:
            if should_refresh:
                with st.spinner("Refreshing XAUUSD across 5m, 1H, 4H and Daily..."):
                    gold_analysis = calculate_gold_analysis()
                    gold_decision = calculate_gold_decision(gold_analysis)

                st.session_state[cache_key] = {
                    "fetched_at": time.time(),
                    "analysis": gold_analysis,
                    "decision": gold_decision,
                }
            else:
                gold_analysis = cached["analysis"]
                gold_decision = cached["decision"]

            fetched_at = st.session_state[cache_key]["fetched_at"]
            age_seconds = max(0, int(time.time() - fetched_at))
            st.caption(
                f"Gold analysis refreshed {age_seconds}s ago • "
                "manual Refresh Gold bypasses the 5-minute cache"
            )

            bias = gold_decision["bias"]
            state = gold_decision["entry_state"]
            alignment = gold_decision["trend_alignment"]
            confirmations = gold_decision["confirmations"]
            required = 5
            latest_price = gold_analysis["quote"]

            c1, c2, c3, c4 = st.columns(4)

            with c1:
                st.metric("XAUUSD", f"${latest_price:,.2f}")

            with c2:
                st.metric("1–2 Day Bias", bias)

            with c3:
                st.metric("Trend Alignment", alignment)

            with c4:
                st.metric(
                    "Entry State",
                    f"{state} • {confirmations}/{required}",
                )

            if state == "READY":
                st.success(
                    f"{bias} setup is READY: higher-timeframe bias and "
                    "lower-timeframe confirmation are aligned."
                )
            elif bias in ("LONG", "SHORT"):
                st.warning(
                    f"{bias} bias, but entry is WATCH. "
                    f"Only {confirmations}/{required} lower-timeframe "
                    "confirmations are currently aligned."
                )
            else:
                st.info(
                    "Higher-timeframe evidence is mixed. No directional trade "
                    "candidate is active."
                )

            # Higher-timeframe evidence.
            st.markdown("#### Higher-Timeframe Evidence")

            tf_cols = st.columns(3)

            for col, key, label in zip(
                tf_cols,
                ["1h", "4h", "1d"],
                ["1 Hour", "4 Hour", "Daily"],
            ):
                snap = gold_analysis["snapshots"][key]

                with col:
                    st.markdown(f"**{label}**")
                    st.write(f"Trend: **{snap['trend']}**")
                    st.write(f"Direction: **{snap['direction']}**")
                    st.write(f"RSI: **{snap['rsi']:.1f}**")
                    st.write(f"MACD: **{snap['macd']}**")
                    st.write(f"MSB: **{snap['msb']}**")

            # Entry confirmation details.
            st.markdown("#### Entry Confirmation")

            e1, e2 = st.columns(2)

            with e1:
                if gold_decision["reasons"]:
                    st.markdown("**Confirming evidence**")
                    for reason in gold_decision["reasons"]:
                        st.write(f"✅ {reason}")
                else:
                    st.write("No 5-minute entry confirmations yet.")

            with e2:
                if gold_decision["warnings"]:
                    st.markdown("**Warnings / conflicts**")
                    for warning in gold_decision["warnings"]:
                        st.write(f"⚠️ {warning}")

            # Trade plan should be shown as a PLAN, not an instruction.
            if gold_decision["entry_zone_low"] is not None:
                st.markdown("#### 📋 Conditional Trade Plan")

                p1, p2, p3, p4 = st.columns(4)

                with p1:
                    st.metric(
                        "Entry Zone",
                        (
                            f"${gold_decision['entry_zone_low']:,.2f} – "
                            f"${gold_decision['entry_zone_high']:,.2f}"
                        ),
                    )

                with p2:
                    st.metric(
                        "Invalidation",
                        f"${gold_decision['invalidation']:,.2f}",
                    )

                with p3:
                    st.metric(
                        "Target 1",
                        f"${gold_decision['target_1']:,.2f}",
                    )

                with p4:
                    st.metric(
                        "Target 2",
                        f"${gold_decision['target_2']:,.2f}",
                    )

                if state != "READY":
                    st.caption(
                        "These are conditional planning levels only. "
                        "The setup is not entry-ready until the Decision Center "
                        "changes to READY."
                    )
                else:
                    st.caption(
                        "READY means the configured technical conditions are "
                        "satisfied; it does not guarantee the trade will succeed."
                    )

            with st.expander("How Gold Decision Center is calculated"):
                st.markdown("""
    **Directional bias** comes primarily from 4H and Daily trend, ADX/DI
    direction and market structure, with 1H providing additional context.

    **Entry timing** is separate. The 5-minute timeframe checks:

    - EMA trend
    - ADX / DI direction
    - MACD
    - Stochastic
    - Market Structure Break

    A LONG or SHORT higher-timeframe bias does **not** mean enter immediately.
    The entry state remains WATCH until enough lower-timeframe confirmation
    appears.

    RSI overextension and conflicting 1H momentum are shown separately as
    warnings rather than being hidden inside a percentage.
    """)

        except Exception as exc:
            st.error(
                "Gold analysis could not be loaded. "
                "The TradingView chart below is still available."
            )
            st.caption(str(exc))

        st.subheader("📈 XAUUSD Chart")

        gold_interval = st.selectbox(
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
            key="gold_tv_interval",
        )

        gold_config = {
            "autosize": True,
            "symbol": "OANDA:XAUUSD",
            "interval": gold_interval[1],
            "timezone": "exchange",
            "theme": "dark",
            "style": "1",
            "locale": "en",
            "withdateranges": True,
            "hide_side_toolbar": False,
            "hide_top_toolbar": False,
            "hide_legend": False,
            "allow_symbol_change": False,
            "save_image": True,
            "details": False,
            "hotlist": False,
            "calendar": False,
            "studies": ["Volume@tv-basicstudies"],
            "support_host": "https://www.tradingview.com",
        }

        gold_json = json.dumps(gold_config)

        gold_html = f"""
        <html>
        <head>
            <style>
                html, body {{
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
                <div class="tradingview-widget-container__widget"></div>
                <script
                    type="text/javascript"
                    src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js"
                    async
                >
                {gold_json}
                </script>
            </div>
        </body>
        </html>
        """

        components.html(
            gold_html,
            height=820,
            scrolling=False,
        )

        with st.expander("Planned Gold AI features"):
            st.markdown("""
    - 1H / 4H / Daily trend
    - RSI / MACD / Stochastic / ADX
    - MSB / Order Blocks
    - Support / Resistance
    - LONG / SHORT / WAIT bias
    - Closed-candle entry confirmation
    - Entry Zone / Invalidation / Target 1 / Target 2
    - Risk / Reward
    """)

