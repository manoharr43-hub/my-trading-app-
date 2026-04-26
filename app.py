import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V42", layout="wide")
st.title("🚀 NSE AI PRO V42 – SMART MONEY SYSTEM")

# =============================
# STOCK LIST
# =============================
sectors = {
    "BANKING": ["HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","AXISBANK.NS"],
    "IT": ["INFY.NS","TCS.NS","WIPRO.NS"],
    "AUTO": ["TATAMOTORS.NS","MARUTI.NS"],
    "FMCG": ["ITC.NS","HINDUNILVR.NS"],
    "ENERGY": ["RELIANCE.NS","ONGC.NS"]
}

sector = st.selectbox("📂 Select Sector", list(sectors.keys()))
stock = st.selectbox("📈 Select Stock", sectors[sector])
interval = st.selectbox("🕒 Timeframe", ["5m","15m","1h"])

# =============================
# DATA LOAD
# =============================
df = yf.download(stock, period="3d", interval=interval)

if df.empty:
    st.error("No Data Found")
    st.stop()

# Fix MultiIndex
if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)

df = df.dropna()

# =============================
# INDICATORS
# =============================
df["EMA9"] = df["Close"].ewm(span=9).mean()
df["EMA21"] = df["Close"].ewm(span=21).mean()

# RSI
delta = df["Close"].diff()
gain = np.where(delta > 0, delta, 0)
loss = np.where(delta < 0, -delta, 0)
avg
