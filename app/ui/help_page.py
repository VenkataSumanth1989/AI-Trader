import math
import streamlit as st

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

    st.subheader("🚦 Closed-Candle Trade State")

    with st.expander("WAITING / CANDIDATE / ENTRY READY / INVALIDATED"):
        st.markdown("""
AI-Trader separates **live price movement** from the **trade decision**.

- **WAITING:** no completed 5-minute candle has confirmed the entry.
- **CANDIDATE:** one completed candle has confirmed the same entry direction.
- **ENTRY READY:** two consecutive completed 5-minute candles confirmed the same direction.
- **INVALIDATED:** an existing ENTRY READY signal lost sufficient closed-candle strength or changed direction.

**Why this matters**
- The current 5-minute candle can move rapidly and make RSI, MACD and other indicators fluctuate.
- AI-Trader therefore uses the **last completed 5-minute candle** for setup and entry confirmation.
- Live price is still displayed separately.
- Once ENTRY READY, a small confidence drop does not instantly cancel the signal. The current keep threshold is **60%**.

This reduces rapid `BUY → WAIT → BUY → WAIT` behavior caused by an unfinished candle.
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

    st.subheader("💹 Market Quote vs Analysis Price")

    with st.expander("Why the two prices can be different"):
        st.markdown("""
- **Market Quote:** latest price Yahoo exposes, including pre-market, after-hours, or overnight when available.
- **Analysis Price:** last completed regular-session 5-minute candle used by AI-Trader's setup and entry calculations.
- Extended-hours quotes can move while the Analysis Price remains unchanged.
- AI-Trader intentionally does **not** recalculate RSI/MACD/MSB/Trade Plan from every overnight quote.
- If Yahoo does not expose a newer extended-hours quote through yfinance, the app shows the quote as unavailable rather than pretending the last regular candle is live.

This separation prevents a moving overnight quote from continuously changing the technical decision engine.
""")

    st.subheader("📋 Trade Plan")

    with st.expander("Entry Zone / Invalidation / Targets"):
        st.markdown("""
- **READY:** swing bias and closed-candle entry confirmation agree.
- **WATCH:** a LONG/SHORT bias exists, but entry confirmation is not ready.
- **INVALID:** the current closed-candle state conflicts with or invalidates the swing bias.
- **NO SETUP:** there is no clear 1–2 day LONG or SHORT bias.

**Entry Zone**
- A small ATR-based zone around the last completed 5-minute close.
- It is meant to discourage chasing price away from the confirmed setup.

**Invalidation**
- LONG plans prefer a level below nearby 1H/4H support.
- SHORT plans prefer a level above nearby 1H/4H resistance.
- If no useful structural level is available, an ATR fallback is used.

**Targets**
- Target 1 = **1.5R**
- Target 2 = **2.5R**

`R` is the planned risk between entry and invalidation.

A READY plan means the technical rules are aligned. It is not a guarantee that the trade will succeed.
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