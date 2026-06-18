import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz

st.set_page_config(page_title="🔥 NSE PRO CHoCH Finder", layout="wide")

st.title("🔥 NSE PRO CHoCH Finder (15m)")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.markdown(f"### 🕒 Live Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")

# --- Load NSE500 Stocks ---
@st.cache_data(ttl=3600)
def load_nse500():
    import requests, io
    url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    df = pd.read_csv(io.StringIO(requests.get(url).text))
    return sorted(df["Symbol"].dropna().unique().tolist())

stocks = load_nse500()

# --- CHoCH / BOS Detection ---
def detect_character_change(df):
    if len(df) < 30:
        return None
    df["Local_High"] = df["High"].rolling(10, center=True).max()
    df["Local_Low"] = df["Low"].rolling(10, center=True).min()
    last_high = df["Local_High"].ffill().iloc[-2]
    last_low = df["Local_Low"].ffill().iloc[-2]
    close = df["Close"].iloc[-1]
    ema20 = df["Close"].ewm(span=20).mean().iloc[-1]
    ema50 = df["Close"].ewm(span=50).mean().iloc[-1]
    bullish = ema20 > ema50
    if close > last_high and bullish:
        return "BOS 📈"
    elif close < last_low and not bullish:
        return "BOS 📉"
    elif close > last_high and not bullish:
        return "CHOCH 🔄 (Bullish Reversal)"
    elif close < last_low and bullish:
        return "CHOCH 🔄 (Bearish Reversal)"
    else:
        return "Range ➖"

# --- Run Scan ---
if st.button("🚀 RUN CHoCH SCAN"):
    results = []
    for s in stocks[:50]:  # limit for demo
        df = yf.download(f"{s}.NS", period="10d", interval="15m", auto_adjust=True, progress=False)
        if df.empty: continue
        signal = detect_character_change(df)
        if signal and "CHOCH" in signal or "BOS" in signal:
            results.append({"Stock": s, "Signal": signal, "Close": round(df["Close"].iloc[-1], 2)})
    if results:
        st.dataframe(pd.DataFrame(results).sort_values("Signal"), use_container_width=True)
    else:
        st.warning("⚠️ No CHoCH/BOS signals found.")
