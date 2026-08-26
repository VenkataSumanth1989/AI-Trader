import streamlit as st

from app.ui.stock_page import render_stock_page
from app.ui.gold_page import render_gold_page
from app.ui.help_page import render_help_page


st.set_page_config(
    page_title="AI-Trader",
    page_icon="📈",
    layout="wide",
)

page = st.sidebar.radio(
    "Navigation",
    [
        "📈 Analysis",
        "🥇 Gold (XAUUSD)",
        "❓ Help / Indicator Guide",
    ],
)

if page == "📈 Analysis":
    render_stock_page()
elif page == "🥇 Gold (XAUUSD)":
    render_gold_page()
else:
    render_help_page()
