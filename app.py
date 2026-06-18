# ============================================
# 🚀 NSE PRO CHoCH Institutional Scanner V1
# ============================================

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
import io

# ============================================
# PAGE CONFIG
# ============================================

st.set_page_config(page_title="🚀 NSE PRO CHoCH Scanner", layout="wide")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE PRO CHoCH Institutional Scanner")
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
        return "Range ➖"

# ============================================
# SCAN FUNCTION
# ============================================

def run_scan():
    results = []
    for s in stocks:
        try:
            df = yf.download(f"{s}.NS", period="10d", interval="15m", auto_adjust=True, progress=False)
            if df.empty: 
                continue
            signal = detect_character_change(df)
            if signal and ("CHOCH" in signal or "BOS" in signal):
                results.append({
                    "Stock": s,
                    "Signal": signal,
                    "Close": round(float(df["Close"].iloc[-1]), 2),
                    "EMA20": round(float(df["Close"].ewm(span=20).mean().iloc[-1]), 2),
                    "EMA50": round(float(df["Close"].ewm(span=50).mean().iloc[-1]), 2)
                })
        except Exception as e:
            continue
    return pd.DataFrame(results)

# ============================================
# UI BUTTON
# ============================================

if st.button("🚀 RUN NSE500 CHoCH SCAN"):
    df = run_scan()
    if not df.empty:
        st.subheader("🔥 Active CHoCH / BOS Signals (15m)")
        st.dataframe(df, use_container_width=True)
        # Download Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="CHoCH_Signals")
        st.download_button("📥 Download Excel Report", data=buffer.getvalue(), file_name="NSE500_CHoCH_Scanner.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.warning("⚠️ No CHoCH/BOS signals found.")
