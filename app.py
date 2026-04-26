import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="NSE AI PRO V23 STABLE", layout="wide")
st.title("🚀 NSE AI PRO V23 - Professional Terminal")

# Auto-refresh every 1 minute
st_autorefresh(interval=60000, key="refresh")

# =============================
# SECTOR-WISE STOCK DATA
# =============================
sectors = {
    "NIFTY 50": ["RELIANCE", "HDFCBANK", "ICICIBANK", "INFY", "TCS", "SBIN", "BHARTIARTL", "ITC", "HINDUNILVR", "LT"],
    "BANK NIFTY": ["SBIN", "HDFCBANK", "ICICIBANK", "AXISBANK", "KOTAKBANK", "INDUSINDBK", "AUBANK", "FEDERALBNK", "IDFCFIRSTB", "PNB"],
    "IT": ["TCS", "INFY", "WIPRO", "HCLTECH", "LTIM", "TECHM", "PERSISTENT", "COFORGE", "MPHASIS"],
    "AUTO": ["TATA MOTORS", "M&M", "MARUTI", "BAJAJ-AUTO", "HEROMOTOCO", "EICHERMOT", "TVSMOTOR", "ASHOKLEY"],
    "PHARMA": ["SUNPHARMA", "CIPLA", "DRREDDY", "DIVISLAB", "TORNTPHARM", "MANKIND", "AUROPHARMA", "LUPIN"],
    "METAL": ["TATASTEEL", "JINDALSTEL", "HINDALCO", "JSWSTEEL", "VEDL", "NMDC", "SAIL"]
}

# =============================
# SIDEBAR SETTINGS
# =============================
st.sidebar.header("⚙️ Market Settings")

selected_sector = st.sidebar.selectbox("📂 Select Sector", list(sectors.keys()))
stock_list = sectors[selected_sector]
selected_stock = st.sidebar.selectbox("📈 Select Stock", stock_list)

interval = st.sidebar.selectbox("🕒 Timeframe", ["5m", "15m", "1h", "1d"])

# =============================
# DATA LOAD ENGINE (With Auto .NS Suffix)
# =============================
@st.cache_data(ttl=60)
def load_data(symbol, interval):
    try:
        # NSE stocks need .NS suffix for yfinance
        ticker = f"{symbol.replace(' ', '')}.NS"
        df = yf.Ticker(ticker).history(period="5d", interval=interval)
        if df.empty:
            return pd.DataFrame()
        df.index = df.index.tz_localize(None) # Remove timezone for Plotly
        return df
    except Exception as e:
        return pd.DataFrame()

df = load_data(selected_stock, interval)

# =============================
# DATA CHECK
# =============================
if df.empty:
    st.error(f"❌ Data not available for {selected_stock}. Market may be closed or symbol error.")
    st.stop()

# =============================
# PROFESSIONAL INDICATORS
# =============================
# 1. EMAs
df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()

# 2. Session-Wise VWAP (Resets daily)
df['Date'] = df.index.date
df['TP'] = (df['High'] + df['Low'] + df['Close']) / 3
df['PV'] = df['TP'] * df['Volume']
df['VWAP'] = df.groupby('Date')['PV'].transform('cumsum') / df.groupby('Date')['Volume'].transform('cumsum')

# =============================
# ADVANCED SIGNAL LOGIC
# =============================
last = df.iloc[-1]
prev = df.iloc[-2]

signal = "NEUTRAL"
color = "white"

# Buying Condition: Price > VWAP AND EMA20 > EMA50
if last['Close'] > last['VWAP'] and last['EMA20'] > last['EMA50']:
    signal = "STRONG BUY"
    color = "#00ff00" # Green
# Selling Condition: Price < VWAP AND EMA20 < EMA50
elif last['Close'] < last['VWAP'] and last['EMA20'] < last['EMA50']:
    signal = "STRONG SELL"
    color = "#ff4b4b" # Red

# =============================
# UI - LIVE METRICS
# =============================
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Current Price", f"₹{last['Close']:.2f}")
with m2:
    st.metric("VWAP", f"₹{last['VWAP']:.2f}")
with m3:
    st.write("Signal Status")
    st.markdown(f"<h3 style='color:{color}; margin-top:-15px;'>{signal}</h3>", unsafe_allow_html=True)
with m4:
    vol_avg = df['Volume'].mean()
    vol_change = ((last['Volume'] - vol_avg) / vol_avg) * 100
    st.metric("Volume Spike", f"{vol_change:.1f}%")

# =============================
# MULTI-CHART (Price + Volume)
# =============================
fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                    vertical_spacing=0.05, 
                    row_heights=[0.7, 0.3])
