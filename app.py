import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="🔥 NSE AI PRO V44", layout="wide")
st.title("🚀 NSE AI PRO V44 – PRECISION MODE")

# =============================
# STOCKS
# =============================
stocks = ["HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","RELIANCE.NS","INFY.NS","TCS.NS"]
stock = st.selectbox("📈 Select Stock", stocks)
interval = st.selectbox("🕒 Timeframe", ["5m","15m"])

# =============================
# DATA
# =============================
df = yf.download(stock, period="3d", interval=interval, progress=False)

if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)

df = df.dropna().reset_index()

# =============================
# INDICATORS
# =============================

# EMA
df["EMA9"] = df["Close"].ewm(span=9).mean()
df["EMA21"] = df["Close"].ewm(span=21).mean()

# RSI
delta = df["Close"].diff()
gain = delta.clip(lower=0)
loss = -delta.clip(upper=0)
rs = gain.rolling(14).mean() / loss.rolling(14).mean()
df["RSI"] = 100 - (100/(1+rs))
df["RSI"] = df["RSI"].fillna(50)

# VWAP
df["VWAP"] = (df["Volume"]*(df["High"]+df["Low"]+df["Close"])/3).cumsum()/df["Volume"].cumsum()

# Volume Spike
df["Vol_Avg"] = df["Volume"].rolling(20).mean().fillna(0)
df["Big"] = df["Volume"] > df["Vol_Avg"]*2

# Trend
df["Trend"] = np.where(df["Close"] > df["EMA21"], "UP", "DOWN")

# =============================
# SIGNAL (STRICT FILTER)
# =============================
signals = [""]

for i in range(1, len(df)):

    strong_buy = (
        df["EMA9"][i] > df["EMA21"][i] and
        df["Close"][i] > df["VWAP"][i] and
        df["RSI"][i] > 60 and
        df["Trend"][i] == "UP" and
        df["Big"][i]
    )

    strong_sell = (
        df["EMA9"][i] < df["EMA21"][i] and
        df["Close"][i] < df["VWAP"][i] and
        df["RSI"][i] < 40 and
        df["Trend"][i] == "DOWN" and
        df["Big"][i]
    )

    if strong_buy:
        signals.append("🔥 STRONG BUY")
    elif strong_sell:
        signals.append("❌ STRONG SELL")
    else:
        signals.append("")

df["Signal"] = signals

# =============================
# ENTRY SYSTEM
# =============================
df["Entry"] = df["Close"]
df["SL"] = np.where(df["Signal"].str.contains("BUY"), df["Close"]*0.995,
           np.where(df["Signal"].str.contains("SELL"), df["Close"]*1.005, 0))

df["Target"] = np.where(df["Signal"].str.contains("BUY"), df["Close"]*1.015,
               np.where(df["Signal"].str.contains("SELL"), df["Close"]*0.985, 0))

# =============================
# LIVE
# =============================
st.subheader("📊 LIVE")

latest = df.iloc[-1]

st.metric("Price", round(latest["Close"],2))
st.metric("RSI", round(latest["RSI"],2))
st.metric("Signal", latest["Signal"])

# =============================
# BACKTEST
# =============================
st.subheader("📅 BACKTEST")

st.dataframe(df[df["Signal"]!=""][["Datetime","Close","Signal","Entry","SL","Target"]].tail(15))

# =============================
# CHART
# =============================
fig = go.Figure()

fig.add_trace(go.Candlestick(
    x=df["Datetime"],
    open=df["Open"],
    high=df["High"],
    low=df["Low"],
    close=df["Close"]
))

sig_df = df[df["Signal"]!=""]

fig.add_trace(go.Scatter(
    x=sig_df["Datetime"],
    y=sig_df["Close"],
    mode="markers",
    name="Signals"
))

st.plotly_chart(fig, use_container_width=True)
