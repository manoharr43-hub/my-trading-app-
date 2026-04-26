import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time
from datetime import datetime
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="NSE AI PRO V23.2", layout="wide")
st.title("🚀 NSE AI PRO V23.2 - TIME FIXED VERSION")

st_autorefresh(interval=180000, key="refresh")

# =============================
# STOCK LIST
# =============================
stocks = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "AXISBANK"]

# =============================
# DATA LOADER
# =============================
@st.cache_data(ttl=120)
def load_data(stock):
    df = yf.download(stock + ".NS", period="7d", interval="5m", progress=False)

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    return df

# =============================
# CLEAN TIME FUNCTION
# =============================
def clean_session(df):
    df = df.copy()

    # remove timezone
    df.index = pd.to_datetime(df.index).tz_localize(None)

    # keep only NSE session
    df = df.between_time("09:15", "15:30")

    return df

# =============================
# INDICATORS
# =============================
def indicators(df):
    df = df.copy()

    df["EMA20"] = df["Close"].ewm(span=20).mean()
    df["EMA50"] = df["Close"].ewm(span=50).mean()

    df["AvgVol"] = df["Volume"].rolling(20).mean()

    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    rs = gain.rolling(14).mean() / (loss.rolling(14).mean() + 1e-9)
    df["RSI"] = 100 - (100 / (1 + rs))

    return df

# =============================
# SMART ENGINE
# =============================
def smart_engine(df, stock):
    df = indicators(df)

    signals = []
    last = None

    for i in range(30, len(df)):
        row = df.iloc[i]
        price = float(row["Close"])

        sig = None

        if row["Volume"] > row["AvgVol"] * 2:
            sig = "🔥 BIG BUY" if row["Close"] > row["Open"] else "💀 BIG SELL"

        elif row["EMA20"] > row["EMA50"] and row["RSI"] > 55:
            sig = "🟢 BUY"

        elif row["EMA20"] < row["EMA50"] and row["RSI"] < 45:
            sig = "🔴 SELL"

        if sig and sig != last:
            last = sig

            signals.append({
                "Stock": stock,
                "Signal": sig,
                "Price": round(price, 2),
                "Time": df.index[i]
            })

    return signals

# =============================
# LIVE SCAN
# =============================
if st.button("🚀 LIVE SCAN"):

    results = []
    today = pd.to_datetime("today").date()

    for s in stocks:
        time.sleep(1)

        df = load_data(s)

        if not df.empty:

            # 🔥 SESSION FILTER APPLY
            df = clean_session(df)

            sigs = smart_engine(df, s)

            # 🔥 TODAY ONLY FILTER
            for x in sigs:
                if pd.to_datetime(x["Time"]).date() == today:
                    results.append(x)

    # =============================
    # FORMAT + SERIAL FIX
    # =============================
    if results:
        df_live = pd.DataFrame(results)

        # 🔥 CLEAN TIME FORMAT (IMPORTANT FIX)
        df_live["Time"] = pd.to_datetime(df_live["Time"]).dt.strftime("%I:%M %p")

        df_live = df_live.sort_values("Time")
        df_live.reset_index(drop=True, inplace=True)
        df_live.index = df_live.index + 1

        st.session_state.live = df_live

# =============================
# DISPLAY LIVE
# =============================
if "live" in st.session_state:

    st.subheader("📡 LIVE SIGNALS (09:15 AM – 03:30 PM ONLY)")

    st.dataframe(st.session_state.live, use_container_width=True)
