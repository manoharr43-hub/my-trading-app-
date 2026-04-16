import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V8", layout="wide")
st_autorefresh(interval=60000, key="refresh")

st.title("🚀 MANOHAR NSE AI PRO V8 TERMINAL")
st.markdown("---")

# =============================
# FAST DATA LOADER (CACHE)
# =============================
@st.cache_data(ttl=60)
def get_data(symbol):
    try:
        return yf.download(symbol + ".NS", period="5d", interval="15m", progress=False)
    except:
        return None

# =============================
# DIRECTION ENGINE
# =============================
def get_direction(signal):
    if signal == "🚀 CONFIRMED BUY":
        return "🟢 UP"
    elif signal == "💀 CONFIRMED SELL":
        return "🔴 DOWN"
    elif "FAILED SELL" in signal:
        return "🟢 UP"
    elif "FAILED BUY" in signal:
        return "🔴 DOWN"
    else:
        return "⚪ WAIT"

# =============================
# AI ANALYSIS ENGINE
# =============================
def analyze(df):

    if df is None or len(df) < 20:
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

    # ================= TREND =================
    trend = "🟢 BULLISH" if e20_v > e50_v else "🔴 BEARISH"

    # ================= BIG PLAYER =================
    if curr_vol > avg_vol * 2:
        player = "🔥 INSTITUTIONAL ENTRY"
    elif curr_vol > avg_vol * 1.5:
        player = "🐋 SMART MONEY"
    else:
        player = "💤 NORMAL"

    # ================= RISK =================
    recent_high = high.iloc[-10:].max()
    recent_low = low.iloc[-10:].min()

    risk = recent_high - recent_low
    if risk <= 0:
        risk = price * 0.01

    # ================= SIGNAL =================
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

    # ================= MOMENTUM SCORE =================
    try:
        momentum = (price - close.iloc[-5]) / price * 100
        vol_score = curr_vol / avg_vol
        ema_gap = abs(e20_v - e50_v) / price * 100

        score = (momentum * 0.3) + (vol_score * 20 * 0.4) + (ema_gap * 0.3)
        score = min(100, round(score, 2))
    except:
        score = 0

    return trend, signal, player, round(entry,2), round(sl,2), round(target,2), score

# =============================
# SECTORS
# =============================
sectors = {
    "Nifty 50": ["RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN"],
    "Banking": ["SBIN","AXISBANK","KOTAKBANK","HDFCBANK","ICICIBANK"],
    "Auto": ["TATAMOTORS","MARUTI","M&M","HEROMOTOCO"],
    "IT": ["TCS","INFY","WIPRO","HCLTECH"],
    "Pharma": ["SUNPHARMA","DRREDDY","CIPLA"]
}

# =============================
# UI
# =============================
sector = st.selectbox("📂 Select Sector", list(sectors.keys()))
stocks = sectors[sector]

if st.button("🔍 START PRO V8 SCANNER", use_container_width=True):

    results = []
    breakout = []

    with st.spinner("AI Scanning Market..."):

        for s in stocks:

            df = get_data(s)

            if df is None or df.empty:
                continue

            res = analyze(df)

            if res:
                trend, signal, player, entry, sl, target, score = res

                results.append({
                    "Stock": s,
                    "Price": round(df["Close"].iloc[-1],2),
                    "Trend": trend,
                    "Signal": signal,
                    "Big Player": player,
                    "Entry": entry,
                    "SL": sl,
                    "Target": target,
                    "Score": score,
                    "Direction": get_direction(signal),
                    "Time": df.index[-1].strftime("%H:%M")
                })

            # ================= BREAKOUT ENGINE =================
            try:
                opening = df.between_time("09:15", "09:30")

                if
