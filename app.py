import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO FINAL", layout="wide")
st_autorefresh(interval=60000, key="refresh")

st.title("🚀 MANOHAR NSE AI PRO - FINAL STABLE SYSTEM")
st.markdown("---")

# =============================
# DATA LOADER
# =============================
@st.cache_data(ttl=60)
def load_stock(symbol):
    try:
        return yf.download(symbol + ".NS", period="5d", interval="15m", progress=False)
    except:
        return None

# =============================
# SECTORS (FULL SAFE - NO BROKEN STRINGS)
# =============================
sectors = {
    "NIFTY 50": [
        "RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK",
        "SBIN","ITC","LT","AXISBANK","BHARTIARTL"
    ],

    "BANKING": [
        "SBIN","HDFCBANK","ICICIBANK","AXISBANK","KOTAKBANK",
        "PNB","BANKBARODA","CANBK","FEDERALBNK"
    ],

    "AUTO": [
        "TATAMOTORS","MARUTI","M&M","HEROMOTOCO",
        "EICHERMOT","ASHOKLEY","TVSMOTOR","BAJAJ-AUTO"
    ],

    "METAL": [
        "TATASTEEL","JSWSTEEL","HINDALCO","JINDALSTEL",
        "SAIL","NATIONALUM","VEDL"
    ],

    "IT": [
        "TCS","INFY","WIPRO","HCLTECH","TECHM",
        "LTIM","COFORGE","MPHASIS"
    ],

    "PHARMA": [
        "SUNPHARMA","DRREDDY","CIPLA","DIVISLAB",
        "APOLLOHOSP","BIOCON","LUPIN"
    ],

    "OIL_GAS": [
        "RELIANCE","ONGC","IOC","BPCL","GAIL"
    ],

    "ENERGY": [
        "ADANIGREEN","ADANIPOWER","NTPC","POWERGRID","TATAPOWER"
    ],

    "INFRA": [
        "LT","IRB","NBCC","DLF","GMRINFRA"
    ],

    "CHEMICALS": [
        "PIDILITIND","DEEPAKNTR","UPL","ATUL","AARTIIND"
    ]
}

# =============================
# ANALYSIS ENGINE
# =============================
def analyze(df):

    if df is None or df.empty or len(df) < 20:
        return None

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    vol = df["Volume"]

    e20 = close.ewm(span=20).mean()
    e50 = close.ewm(span=50).mean()

    price = float(close.iloc[-1])
    e20_v = float(e20.iloc[-1])
    e50_v = float(e50.iloc[-1])

    avg_vol = vol.rolling(20).mean().iloc[-1]
    curr_vol = vol.iloc[-1]

    if pd.isna(avg_vol) or avg_vol == 0:
        avg_vol = curr_vol

    trend = "🟢 BULLISH" if e20_v > e50_v else "🔴 BEARISH"

    if curr_vol > avg_vol * 2:
        player = "🔥 INSTITUTIONAL"
    elif curr_vol > avg_vol * 1.5:
        player = "🐋 SMART MONEY"
    else:
        player = "💤 NORMAL"

    recent_high = high.iloc[-10:].max()
    recent_low = low.iloc[-10:].min()

    risk = recent_high - recent_low
    if risk <= 0:
        risk = price * 0.01

    signal = "WAIT"
    entry = sl = target = 0

    if e20_v > e50_v and curr_vol > avg_vol:
        signal = "🚀 CONFIRMED BUY"
        entry = price
        sl = price - risk * 0.5
        target = price + risk

    elif e20_v < e50_v and curr_vol > avg_vol:
        signal = "💀 CONFIRMED SELL"
        entry = price
        sl = price + risk * 0.5
        target = price - risk

    return trend, signal, player, entry, sl, target

# =============================
# UI
# =============================
sector = st.selectbox("📂 SELECT SECTOR", list(sectors.keys()))
stocks = sectors[sector]

if st.button("🔍 START SCANNER", use_container_width=True):

    results = []

    with st.spinner("Scanning NSE Market..."):

        for s in stocks:

            df = load_stock(s)

            if df is None or df.empty:
                continue

            res = analyze(df)

            if res:
                trend, signal, player, entry, sl, target = res

                results.append({
                    "Stock": s,
                    "Price": round(df["Close"].iloc[-1],2),
                    "Trend": trend,
                    "Signal": signal,
                    "Big Player": player,
                    "Entry": round(entry,2),
                    "SL": round(sl,2),
                    "Target": round(target,2),
                    "Time": df.index[-1].strftime("%H:%M")
                })

    if results:
        st.dataframe(pd.DataFrame(results), use_container_width=True)
    else:
        st.warning("No Data Found")

# =============================
# FOOTER
# =============================
st.markdown("---")
st.success("🔥 NSE AI PRO FINAL - ZERO ERROR STABLE SYSTEM RUNNING")
