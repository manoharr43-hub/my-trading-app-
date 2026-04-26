import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="LIVE NSE PRO SCANNER", layout="wide")
st.title("🚀 NSE AI PRO LIVE SCANNER V1 (Smart Money)")

# 🔥 fast refresh (NOT 1 sec real API, but UI refresh)
st_autorefresh(interval=30000, key="live_refresh")  # 30 sec safe

# =============================
# STOCK LIST
# =============================
stocks = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "AXISBANK"]

# =============================
# DATA LOADER (FAST + SAFE)
# =============================
@st.cache_data(ttl=60)
def get_data(stock):
    try:
        df = yf.download(stock + ".NS", period="5d", interval="5m", progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except:
        return pd.DataFrame()

# =============================
# SMART MONEY ENGINE
# =============================
def smart_signals(df):
    df = df.copy()

    df["EMA20"] = df["Close"].ewm(span=20).mean()
    df["EMA50"] = df["Close"].ewm(span=50).mean()

    df["AvgVol"] = df["Volume"].rolling(20).mean()

    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    rs = gain.rolling(14).mean() / (loss.rolling(14).mean() + 1e-9)
    df["RSI"] = 100 - (100 / (1 + rs))

    latest = df.iloc[-1]

    signal = None

    # 🔥 SMART MONEY LOGIC
    if latest["Volume"] > latest["AvgVol"] * 2:
        signal = "🔥 BIG MONEY BUY" if latest["Close"] > latest["Open"] else "💀 BIG SELL"

    elif latest["EMA20"] > latest["EMA50"] and latest["RSI"] > 55:
        signal = "🟢 STRONG BUY"

    elif latest["EMA20"] < latest["EMA50"] and latest["RSI"] < 45:
        signal = "🔴 STRONG SELL"

    return signal, latest["Close"]

# =============================
# LIVE SCAN ENGINE
# =============================
if st.button("🚀 START LIVE SCAN"):

    results = []

    placeholder = st.empty()

    while True:
        live_data = []

        for s in stocks:
            df = get_data(s)

            if not df.empty:
                sig, price = smart_signals(df)

                if sig:
                    live_data.append({
                        "Stock": s,
                        "Signal": sig,
                        "Price": round(price, 2),
                        "Time": datetime.now().strftime("%H:%M:%S")
                    })

        with placeholder.container():
            st.subheader("📡 LIVE SIGNALS")

            if live_data:
                st.dataframe(pd.DataFrame(live_data), use_container_width=True)
            else:
                st.info("No strong signals right now... waiting smart money")

        time.sleep(30)  # safe refresh (not API spam)
