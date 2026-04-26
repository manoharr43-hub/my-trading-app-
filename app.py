import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="🔥 NSE AI PRO V40", layout="wide")
st.title("🚀 NSE AI PRO V40 – Intraday System")

# =============================
# STOCK LIST (Sector Wise)
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
df = yf.download(stock, period="2d", interval=interval)

if df.empty:
    st.error("No Data Found")
    st.stop()

# =============================
# INDICATORS
# =============================
df["EMA9"] = df["Close"].ewm(span=9).mean()
df["EMA21"] = df["Close"].ewm(span=21).mean()
df["VWAP"] = (df["Volume"] * (df["High"]+df["Low"]+df["Close"])/3).cumsum() / df["Volume"].cumsum()

# Volume spike (Big Player)
df["Vol_Avg"] = df["Volume"].rolling(20).mean()
df["BigPlayer"] = df["Volume"] > df["Vol_Avg"] * 2

# =============================
# SIGNAL LOGIC
# =============================
signals = []

for i in range(1, len(df)):
    buy = df["EMA9"].iloc[i] > df["EMA21"].iloc[i] and df["Close"].iloc[i] > df["VWAP"].iloc[i]
    sell = df["EMA9"].iloc[i] < df["EMA21"].iloc[i] and df["Close"].iloc[i] < df["VWAP"].iloc[i]

    # Reversal
    reversal = (
        (df["EMA9"].iloc[i-1] < df["EMA21"].iloc[i-1] and df["EMA9"].iloc[i] > df["EMA21"].iloc[i]) or
        (df["EMA9"].iloc[i-1] > df["EMA21"].iloc[i-1] and df["EMA9"].iloc[i] < df["EMA21"].iloc[i])
    )

    signal = ""
    if buy:
        signal = "BUY"
    elif sell:
        signal = "SELL"

    if reversal:
        signal = "REVERSAL"

    if df["BigPlayer"].iloc[i]:
        signal += " + BIG PLAYER"

    signals.append(signal)

df = df.iloc[1:]
df["Signal"] = signals

# =============================
# ENTRY / SL / TARGET
# =============================
df["Entry"] = df["Close"]
df["SL"] = df["Close"] * 0.99
df["Target"] = df["Close"] * 1.02

# =============================
# DISPLAY SIGNALS
# =============================
st.subheader("📊 LIVE SIGNALS")

latest = df.iloc[-1]

st.metric("Current Price", round(latest["Close"],2))
st.metric("VWAP", round(latest["VWAP"],2))
st.metric("Signal", latest["Signal"])

# =============================
# BACKTEST TABLE
# =============================
st.subheader("📅 BACKTEST")

backtest = df[["Close","Signal","Entry","SL","Target"]].tail(20)
st.dataframe(backtest)

# =============================
# CHART
# =============================
fig = go.Figure()

fig.add_trace(go.Candlestick(
    x=df.index,
    open=df["Open"],
    high=df["High"],
    low=df["Low"],
    close=df["Close"],
    name="Price"
))

# BUY signals
buy_df = df[df["Signal"].str.contains("BUY", na=False)]
fig.add_trace(go.Scatter(
    x=buy_df.index,
    y=buy_df["Close"],
    mode="markers",
    marker=dict(size=10),
    name="BUY"
))

# SELL signals
sell_df = df[df["Signal"].str.contains("SELL", na=False)]
fig.add_trace(go.Scatter(
    x=sell_df.index,
    y=sell_df["Close"],
    mode="markers",
    marker=dict(size=10),
    name="SELL"
))

# REVERSAL signals
rev_df = df[df["Signal"].str.contains("REVERSAL", na=False)]
fig.add_trace(go.Scatter(
    x=rev_df.index,
    y=rev_df["Close"],
    mode="markers",
    marker=dict(size=12),
    name="REVERSAL"
))

st.plotly_chart(fig, use_container_width=True)
