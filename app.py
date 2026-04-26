import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="NSE AI PRO V23 STABLE", layout="wide")
st.title("🚀 NSE AI PRO V23 - Stable Build")

st_autorefresh(interval=60000, key="refresh")

# =============================
# STOCKS
# =============================
stocks = ["RELIANCE", "HDFCBANK", "INFY", "TCS", "SBIN"]

# =============================
# SIDEBAR
# =============================
st.sidebar.header("⚙️ Settings")
stock = st.sidebar.selectbox("Select Stock", stocks)
interval = st.sidebar.selectbox("Timeframe", ["5m", "15m", "1h"])

# =============================
# DATA LOAD (SAFE)
# =============================
@st.cache_data(ttl=60)
def load_data(symbol, interval):
    try:
        df = yf.Ticker(symbol + ".NS").history(period="5d", interval=interval)
        if df.empty:
            return pd.DataFrame()
        df = df.tz_localize(None)
        return df
    except:
        return pd.DataFrame()

df = load_data(stock, interval)

# =============================
# CHECK DATA
# =============================
if df.empty:
    st.error("❌ Data not loading. Check internet or market hours.")
    st.stop()

# =============================
# INDICATORS
# =============================
df['EMA20'] = df['Close'].ewm(span=20).mean()
df['EMA50'] = df['Close'].ewm(span=50).mean()

tp = (df['High'] + df['Low'] + df['Close']) / 3
df['VWAP'] = (tp * df['Volume']).cumsum() / df['Volume'].cumsum()

# =============================
# SIMPLE SIGNAL
# =============================
last = df.iloc[-1]

signal = "NO TRADE"

if last['Close'] > last['VWAP'] and last['EMA20'] > last['EMA50']:
    signal = "BUY"
elif last['Close'] < last['VWAP'] and last['EMA20'] < last['EMA50']:
    signal = "SELL"

st.subheader(f"📊 Signal: {signal}")

# =============================
# CHART (100% SAFE)
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
