import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V11", layout="wide")
st.title("🚀 NSE AI PRO V11 (ZERO ERROR FINAL)")
st_autorefresh(interval=60000, key="refresh")

# =============================
# SESSION INIT
# =============================
if "live_big" not in st.session_state:
    st.session_state.live_big = []
if "strength" not in st.session_state:
    st.session_state.strength = pd.DataFrame()
if "bt_df" not in st.session_state:
    st.session_state.bt_df = pd.DataFrame()

# =============================
# STOCK LIST
# =============================
stocks = ["HDFCBANK","ICICIBANK","SBIN","RELIANCE","INFY","TCS","ITC","LT","AXISBANK","KOTAKBANK"]

# =============================
# FUNCTIONS
# =============================
def clean_time(ts):
    try:
        return pd.to_datetime(ts).strftime("%I:%M %p").lstrip("0")
    except:
        return ""

@st.cache_data(ttl=60)
def load_data(stock, period="1d"):
    try:
        df = yf.Ticker(stock + ".NS").history(period=period, interval="5m")
        if df is None or df.empty:
            return pd.DataFrame()
        df = df.between_time("09:15","15:30")
        return df.dropna()
    except:
        return pd.DataFrame()

# =============================
# BIG PLAYER LOGIC V11
# =============================
def big_player(df, stock):
    if df is None or df.empty or len(df) < 30:
        return []

    df = df.copy()

    # EMA
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    # VWAP (safe)
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    df['VWAP'] = (typical_price * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1)

    # RSI (safe)
    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / (avg_loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))

    # Volume
    df['AvgVol'] = df['Volume'].rolling(20).mean()

    # Candle strength
    df['Body'] = abs(df['Close'] - df['Open'])
    df['Range'] = df['High'] - df['Low']
    df['StrongCandle'] = df['Body'] > (df['Range'] * 0.6)

    entries = []

    for i in range(25, len(df)):
        try:
            price = df['Close'].iloc[i]

            score = 0
            if price > df['EMA20'].iloc[i]: score += 1
            if price > df['EMA50'].iloc[i]: score += 1
            if price > df['VWAP'].iloc[i]: score += 1
            if df['RSI'].iloc[i] > 60: score += 1
            if df['Volume'].iloc[i] > df['AvgVol'].iloc[i]*3: score += 1

            confidence = f"{score}/5"

            # BIG BUY
            if (
                df['Volume'].iloc[i] > df['AvgVol'].iloc[i]*2.5 and
                price > df['EMA20'].iloc[i] > df['EMA50'].iloc[i] and
                price > df['VWAP'].iloc[i] and
                df['RSI'].iloc[i] > 55 and
                df['StrongCandle'].iloc[i]
            ):
                entries.append({
                    "Stock": stock,
                    "Type": "BIG BUY",
                    "Price": round(price,2),
                    "TimeRaw": df.index[i],
                    "Time": clean_time(df.index[i]),
                    "Confidence": confidence
                })

            # BIG SELL
            elif (
                df['Volume'].iloc[i] > df['AvgVol'].iloc[i]*2.5 and
                price < df['EMA20'].iloc[i] < df['EMA50'].iloc[i] and
                price < df['VWAP'].iloc[i] and
                df['RSI'].iloc[i] < 45 and
                df
