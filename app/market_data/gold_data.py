import os
import pandas as pd
import requests

BASE_URL = "https://api.twelvedata.com/time_series"

def _get_api_key():
    try:
        import streamlit as st
        key = st.secrets.get("TWELVE_DATA_API_KEY")
        if key:
            return str(key)
    except Exception:
        pass
    key = os.getenv("TWELVE_DATA_API_KEY")
    if key:
        return key
    raise RuntimeError("TWELVE_DATA_API_KEY is not configured.")

def get_xauusd_candles(interval="5min", outputsize=100):
    params = {
        "symbol": "XAU/USD",
        "interval": interval,
        "outputsize": outputsize,
        "apikey": _get_api_key(),
        "format": "JSON",
    }
    response = requests.get(BASE_URL, params=params, timeout=20)
    response.raise_for_status()
    payload = response.json()

    if payload.get("status") == "error":
        raise RuntimeError(
            f"Twelve Data error for XAU/USD {interval}: "
            f"{payload.get('message', 'Unknown error')}"
        )

    values = payload.get("values")
    if not values:
        raise RuntimeError(f"No XAU/USD data returned for {interval}.")

    df = pd.DataFrame(values)
    required = ["datetime", "open", "high", "low", "close"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise RuntimeError(f"Missing columns: {missing}")

    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    for col in ["open", "high", "low", "close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    if "volume" in df.columns:
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce")

    df = df.dropna(subset=required).sort_values("datetime").set_index("datetime")
    df = df.rename(columns={
        "open": "Open", "high": "High", "low": "Low",
        "close": "Close", "volume": "Volume"
    })
    return df

def test_xauusd_intervals():
    results = {}
    for interval in ["5min", "1h", "4h", "1day"]:
        try:
            df = get_xauusd_candles(interval, 10)
            results[interval] = {
                "ok": True,
                "rows": len(df),
                "latest_time": str(df.index[-1]),
                "latest_close": float(df["Close"].iloc[-1]),
            }
        except Exception as exc:
            results[interval] = {"ok": False, "error": str(exc)}
    return results