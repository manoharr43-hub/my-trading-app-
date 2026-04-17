import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="🔥 NSE AI PRO", layout="wide")
st_autorefresh(interval=60000, key="refresh")

st.title("🚀 NSE AI PRO TERMINAL")

# SAFE DATA
def load_stock(s):
    try:
        return yf.download(s + ".NS", period="5d", interval="15m", progress=False)
    except:
        return None

# ANALYSIS (SAME OLD LOGIC)
def analyze(df):
    if df is None or len(df) < 20:
        return None

    close = df["Close"]
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

    trend = "BULLISH" if e20_v > e50_v else "BEARISH"

    signal = "WAIT"
    entry = sl = target = 0

    if e20_v > e50_v and curr_vol > avg_vol:
        signal = "CONFIRMED BUY"
        entry = price
        sl = price * 0.99
        target = price * 1.02

    elif e20_v < e50_v and curr_vol > avg_vol:
        signal = "CONFIRMED SELL"
        entry = price
        sl = price * 1.01
        target = price * 0.98

    return trend, signal, entry, sl, target

# SECTORS (SAME OLD)
sectors = {
    "NIFTY": ["RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK"],
    "BANK": ["SBIN","AXISBANK","KOTAKBANK"],
    "AUTO": ["TATAMOTORS","MARUTI","M&M"],
    "IT": ["TCS","INFY","WIPRO"],
    "PHARMA": ["SUNPHARMA","CIPLA","DRREDDY"]
}

sector = st.selectbox("Sector", list(sectors.keys()))
stocks = sectors[sector]

if st.button("SCAN"):
    out = []

    for s in stocks:
        df = load_stock(s)
        if df is None or df.empty:
            continue

        res = analyze(df)
        if res:
            trend, signal, entry, sl, target = res

            out.append({
                "Stock": s,
                "Price": round(df["Close"].iloc[-1],2),
                "Trend": trend,
                "Signal": signal,
                "Entry": round(entry,2),
                "SL": round(sl,2),
                "Target": round(target,2),
                "Time": df.index[-1].strftime("%H:%M")
            })

    if out:
        st.dataframe(pd.DataFrame(out))
    else:
        st.warning("No Data")

st.markdown("---")
st.success("RUNNING OK")
