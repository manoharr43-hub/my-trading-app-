import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="🔥 NSE AI PRO V41 PRO MAX", layout="wide")
st.title("🚀 NSE AI PRO V41 – PRO MAX")

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

sector = st.selectbox("📂 Sector", list(sectors.keys()))
stock = st.selectbox("📈 Stock", sectors[sector])
interval = st.selectbox("🕒 Timeframe", ["5m","15m","1h"])

# =============================
# DATA
# =============================
df = yf.download(stock, period="2d", interval=interval)

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
avg_gain = pd.Series(gain).rolling(14).mean()
avg_loss = pd.Series(loss).rolling(14).mean()
rs = avg_gain / avg_loss
df["RSI"] = 100 - (100 / (1 + rs))

# VWAP
df["VWAP"] = (df["Volume"]*(df["High"]+df["Low"]+df["Close"])/3).cumsum()/df["Volume"].cumsum()

# Volume Spike
df["Vol_Avg"] = df["Volume"].rolling(20).mean().fillna(0)
df["BigPlayer"] = df["Volume"] > df["Vol_Avg"]*2

# =============================
# SUPER TREND
# =============================
atr = (df["High"] - df["Low"]).rolling(10).mean()
upper = df["Close"] + (atr * 2
