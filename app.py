# ============================================
# 🚀 NSE PRO CHoCH Institutional Scanner V4
# ============================================

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import pytz
import io
import time
from concurrent.futures import ThreadPoolExecutor

# ============================================
# PAGE CONFIG
# ============================================

st.set_page_config(page_title="🚀 NSE PRO CHoCH Scanner V4", layout="wide")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE PRO CHoCH Institutional Scanner V4")
st.markdown(f"### 🕒 LIVE TIME: {now.strftime('%Y-%m-%d %H:%M:%S')}")

# ============================================
# LOAD NSE500 STOCKS
# ============================================

@st.cache_data(ttl=86400)
def load_nse500():
    import requests
    try:
        url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
        df = pd.read_csv(io.StringIO(requests.get(url).text))
        return sorted(df["Symbol"].dropna().unique().tolist())
    except:
        return ["RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","ITC","LT","AXISBANK"]

stocks = load_nse500()

# ============================================
# CHoCH / BOS DETECTION ENGINE
# ============================================

def detect_character_change(df):
    if len(df) < 30:
        return None
    df["Local_High"] = df["High"].rolling(10, center=True).max()
    df["Local_Low"] = df["Low"].rolling(10, center=True).min()
    last_high = float(df["Local_High"].ffill().iloc[-2])
    last_low = float(df["Local_Low"].ffill().iloc[-2])
    close = float(df["Close"].iloc[-1])
    ema20 = df["Close"].ewm(span=20).mean().iloc[-1]
    ema50 = df["Close"].ewm(span=50).mean().iloc[-1]
    bullish = ema20 > ema50

    if close > last_high and bullish:
        return "BOS 📈"
    elif close < last_low and not bullish:
        return "BOS 📉"
    elif close > last_high and not bullish:
        return "CHOCH 🔄 Bullish Reversal"
    elif close < last_low and bullish:
        return "CHOCH 🔄 Bearish Reversal"
    else:
        return None

# ============================================
# SCAN FUNCTION (MULTITHREAD + PROGRESS)
# ============================================

def run_scan():
    results = []
    progress = st.progress(0)
    total = len(stocks)
    with ThreadPoolExecutor(max_workers=10) as executor:
        for i, s in enumerate(stocks):
            try:
                df = yf.download(f"{s}.NS", period="5d", interval="15m", auto_adjust=True, progress=False)
                if df.empty:
                    continue
                signal = detect_character_change(df)
                if signal:
                    results.append({
                        "Stock": s,
                        "Signal": signal,
                        "Close": round(float(df["Close"].iloc[-1]), 2),
                        "EMA20": round(float(df["Close"].ewm(span=20).mean().iloc[-1]), 2),
                        "EMA50": round(float(df["Close"].ewm(span=50).mean().iloc[-1]), 2)
                    })
            except Exception:
                continue
            progress.progress((i + 1) / total)
            time.sleep(0.02)
    progress.empty()
    return pd.DataFrame(results)

# ============================================
# CHART PREVIEW FUNCTION
# ============================================

def show_chart(symbol):
    df = yf.download(f"{symbol}.NS", period="10d", interval="15m", auto_adjust=True, progress=False)
    if df.empty:
        st.warning("⚠️ Chart data not available.")
        return
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name="Candles"
    )])
    fig.update_layout(
        title=f"{symbol} — 15m CHoCH/BOS Chart",
        xaxis_title="Time",
        yaxis_title="Price",
        template="plotly_dark",
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)

# ============================================
# UI BUTTON
# ============================================

if st.button("🚀 RUN NSE500 CHoCH SCAN"):
    st.info("🔍 Scanning all NSE500 stocks for CHoCH/BOS signals...")
    df = run_scan()
    if not df.empty:
        st.success(f"✅ {len(df)} CHoCH/BOS signals found!")
        st.dataframe(df.sort_values("Signal"), use_container_width=True)
        selected = st.selectbox("📊 Select stock to view chart:", df["Stock"].unique())
        if selected:
            show_chart(selected)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="CHoCH_Signals")
        st.download_button("📥 Download Excel Report", data=buffer.getvalue(), file_name="NSE500_CHoCH_Scanner_V4.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.warning("⚠️ No CHoCH/BOS signals found.")
