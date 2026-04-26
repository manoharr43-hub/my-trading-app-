import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="NSE INTRADAY PRO V23", layout="wide")
st.title("⚡ NSE INTRADAY PRO V23")

# =============================
# STOCKS
# =============================
stocks = ["RELIANCE","HDFCBANK","INFY","TCS","SBIN"]

# =============================
# SIDEBAR
# =============================
st.sidebar.header("⚙️ Intraday Settings")
stock = st.sidebar.selectbox("📈 Stock", stocks)
interval = st.sidebar.selectbox("🕒 Timeframe", ["5m","15m"])

# =============================
# DATA (TODAY ONLY)
# =============================
@st.cache_data(ttl=30)
def load_data(symbol, interval):
    try:
        df = yf.Ticker(symbol + ".NS").history(period="1d", interval=interval)
        if df.empty:
            return pd.DataFrame()
        df = df.tz_localize(None)
        return df.reset_index(drop=True)
    except:
        return pd.DataFrame()

df = load_data(stock, interval)

if df.empty:
    st.error("❌ Data not available (market closed / internet issue)")
    st.stop()

# =============================
# INDICATORS
# =============================
df['EMA20'] = df['Close'].ewm(span=20).mean()
df['EMA50'] = df['Close'].ewm(span=50).mean()

tp = (df['High'] + df['Low'] + df['Close']) / 3
df['VWAP'] = (tp * df['Volume']).cumsum() / df['Volume'].cumsum()

df['AvgVol'] = df['Volume'].rolling(20).mean()

# =============================
# SIGNAL LOGIC (INTRADAY)
# =============================
last = df.iloc[-1]

signal = "NO TRADE"

if (
    last['Close'] > last['VWAP'] and
    last['EMA20'] > last['EMA50'] and
    last['Volume'] > last['AvgVol'] * 2
):
    signal = "BUY"

elif (
    last['Close'] < last['VWAP'] and
    last['EMA20'] < last['EMA50'] and
    last['Volume'] > last['AvgVol'] * 2
):
    signal = "SELL"

# =============================
# TIME FILTER
# =============================
current_time = datetime.now().time()

if current_time > datetime.strptime("15:00", "%H:%M").time():
    signal = "NO TRADE"
    st.warning("⚠️ Avoid new trades after 3:00 PM")

# =============================
# SL & TARGET
# =============================
price = round(last['Close'], 2)

if signal == "BUY":
    sl = round(price * 0.995, 2)
    tgt = round(price * 1.01, 2)

elif signal == "SELL":
    sl = round(price * 1.005, 2)
    tgt = round(price * 0.99, 2)
else:
    sl, tgt = None, None

# =============================
# DASHBOARD
# =============================
col1, col2, col3 = st.columns(3)

col1.metric("💰 Price", price)
col2.metric("📊 VWAP", round(last['VWAP'], 2))
col3.metric("⚡ Signal", signal)

if signal != "NO TRADE":
    st.success(f"Entry: {price} | SL: {sl} | Target: {tgt}")

# =============================
# CHART (NO ERROR SAFE)
# =============================
fig = go.Figure()

fig.add_trace(go.Candlestick(
    x=df.index,
    open=df['Open'],
    high=df['High'],
    low=df['Low'],
    close=df['Close']
))

fig.add_trace(go.Scatter(x=df.index, y=df['EMA20'], name="EMA20"))
fig.add_trace(go.Scatter(x=df.index, y=df['EMA50'], name="EMA50"))
fig.add_trace(go.Scatter(x=df.index, y=df['VWAP'], name="VWAP"))

fig.update_layout(
    template="plotly_dark",
    xaxis_rangeslider_visible=False
)

st.plotly_chart(fig, use_container_width=True)
