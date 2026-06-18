# ============================================
# 🚀 NSE PRO CHoCH Institutional Scanner V8
# ============================================

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
import io
import time
from concurrent.futures import ThreadPoolExecutor

# ============================================
# PAGE CONFIG
# ============================================

st.set_page_config(page_title="🚀 NSE PRO CHoCH Scanner V8", layout="wide")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE PRO CHoCH Institutional Scanner V8")
st.markdown(f"### 🕒 LIVE TIME: {now.strftime('%Y-%m-%d %H:%M:%S')}")

# ============================================
# SETTINGS
# ============================================

with st.sidebar:
    st.header("⚙️ Settings")
    sensitivity = st.slider("🔍 Sensitivity (Rolling Window)", 3, 15, 8)
    backtest_days = st.slider("📅 Backtest Days", 1, 30, 5)
    st.caption("Adjust sensitivity & backtest period.")

# ============================================
# STOCK LIST
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

def detect_character_change(df, window):
    if len(df) < 30:
        return None
    df["Local_High"] = df["High"].rolling(window, center=True).max()
    df["Local_Low"] = df["Low"].rolling(window, center=True).min()
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
# BACKTEST FUNCTION
# ============================================

def run_backtest(symbol, days, window):
    df = yf.download(f"{symbol}.NS", period=f"{days}d", interval="15m", auto_adjust=True, progress=False)
    if df.empty:
        return None
    signals = []
    for i in range(window, len(df)):
        sub_df = df.iloc[:i+1]
        signal = detect_character_change(sub_df, window)
        if signal:
            signals.append({
                "Date": sub_df.index[-1],
                "Stock": symbol,
                "Signal": signal,
                "Close": round(float(sub_df["Close"].iloc[-1]), 2)
            })
    return pd.DataFrame(signals)

# ============================================
# SCAN FUNCTION
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
                signal = detect_character_change(df, sensitivity)
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
# MAIN UI
# ============================================

if st.button("🚀 RUN NSE PRO CHoCH SCAN"):
    st.info("🔍 Scanning NSE500 stocks for CHoCH/BOS signals...")
    df = run_scan()
    if not df.empty:
        st.success(f"✅ {len(df)} CHoCH/BOS signals found!")
        st.dataframe(df.sort_values("Signal"), use_container_width=True)

        selected = st.selectbox("📊 Select stock to backtest:", df["Stock"].unique())
        if selected:
            st.info(f"🔄 Running backtest for {selected} ({backtest_days} days)...")
            bt = run_backtest(selected, backtest_days, sensitivity)
            if bt is not None and not bt.empty:
                st.subheader("📈 Backtest Results")
                st.dataframe(bt, use_container_width=True)
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                    bt.to_excel(writer, index=False, sheet_name="Backtest")
                st.download_button("📥 Download Backtest Excel", data=buffer.getvalue(), file_name=f"{selected}_CHoCH_Backtest.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            else:
                st.warning("⚠️ No backtest signals found.")
    else:
        st.warning("⚠️ No CHoCH/BOS signals found.")
