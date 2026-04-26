import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V43", layout="wide")
st.title("🚀 NSE AI PRO V43 – ULTRA STABLE")

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
# DATA
# =============================
df = yf.download(stock, period="3d", interval=interval, progress=False)

if df.empty:
    st.error("No Data Found")
    st.stop()

# Fix MultiIndex
if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)

df = df.dropna().reset_index()

# =============================
# INDICATORS
# =============================

# EMA
df["EMA9"] = df["Close"].ewm(span=9).mean()
df["EMA21"] = df["Close"].ewm(span=21).mean()

# RSI (SAFE)
delta = df["Close"].diff()
gain = delta.clip(lower=0)
loss = -delta.clip(upper=0)

avg_gain = gain.rolling(14, min_periods=14).mean()
avg_loss = loss.rolling(14, min_periods=14).mean()

rs = avg_gain / avg_loss
df["RSI"] = 100 - (100 / (1 + rs))
df["RSI"] = df["RSI"].fillna(50)

# VWAP
df["VWAP"] = (df["Volume"]*(df["High"]+df["Low"]+df["Close"])/3).cumsum()/df["Volume"].cumsum()

# =============================
# SUPER TREND (STABLE)
# =============================
period = 10
multiplier = 3

df["TR"] = np.maximum(
    df["High"] - df["Low"],
    np.maximum(
        abs(df["High"] - df["Close"].shift()),
        abs(df["Low"] - df["Close"].shift())
    )
)

df["ATR"] = df["TR"].rolling(period).mean()

df["UpperBand"] = ((df["High"] + df["Low"]) / 2) + (multiplier * df["ATR"])
df["LowerBand"] = ((df["High"] + df["Low"]) / 2) - (multiplier * df["ATR"])

trend = ["DOWN"]

for i in range(1, len(df)):
    if df["Close"][i] > df["UpperBand"][i-1]:
        trend.append("UP")
    elif df["Close"][i] < df["LowerBand"][i-1]:
        trend.append("DOWN")
    else:
        trend.append(trend[i-1])

df["Trend"] = trend

# =============================
# BIG PLAYER
# =============================
df["Vol_Avg"] = df["Volume"].rolling(20).mean().fillna(0)
df["BigPlayer"] = df["Volume"] > df["Vol_Avg"] * 2

# =============================
# ORB
# =============================
opening_high = df["High"].iloc[:5].max()
opening_low = df["Low"].iloc[:5].min()

# =============================
# SIGNALS
# =============================
signals = [""]

for i in range(1, len(df)):

    buy = (
        df["EMA9"][i] > df["EMA21"][i] and
        df["Close"][i] > df["VWAP"][i] and
        df["RSI"][i] > 55 and
        df["Trend"][i] == "UP" and
        df["Close"][i] > opening_high
    )

    sell = (
        df["EMA9"][i] < df["EMA21"][i] and
        df["Close"][i] < df["VWAP"][i] and
        df["RSI"][i] < 45 and
        df["Trend"][i] == "DOWN" and
        df["Close"][i] < opening_low
    )

    reversal = (
        (df["EMA9"][i-1] < df["EMA21"][i-1] and df["EMA9"][i] > df["EMA21"][i]) or
        (df["EMA9"][i-1] > df["EMA21"][i-1] and df["EMA9"][i] < df["EMA21"][i])
    )

    sig = ""

    if buy:
        sig = "🔥 STRONG BUY"
    elif sell:
        sig = "❌ STRONG SELL"
    elif reversal:
        sig = "🔄 REVERSAL"

    if df["BigPlayer"][i]:
        sig += " + 🐋"

    signals.append(sig)

df["Signal"] = signals

# =============================
# ENTRY SYSTEM
# =============================
df["Entry"] = df["Close"]
df["SL"] = df["Close"] * 0.995
df["Target"] = df["Close"] * 1.015

# =============================
# LIVE
# =============================
st.subheader("📊 LIVE SIGNAL")

latest = df.iloc[-1]

st.metric("Price", round(latest["Close"],2))
st.metric("RSI", round(latest["RSI"],2))
st.metric("Trend", latest["Trend"])
st.metric("Signal", latest["Signal"])

# =============================
# BACKTEST
# =============================
st.subheader("📅 BACKTEST")

bt = df[["Datetime","Close","Signal","Entry","SL","Target"]].tail(25)
st.dataframe(bt)

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

buy_df = df[df["Signal"].str.contains("BUY", na=False)]
sell_df = df[df["Signal"].str.contains("SELL", na=False)]
rev_df = df[df["Signal"].str.contains("REVERSAL", na=False)]

fig.add_trace(go.Scatter(x=buy_df["Datetime"], y=buy_df["Close"], mode="markers", name="BUY"))
fig.add_trace(go.Scatter(x=sell_df["Datetime"], y=sell_df["Close"], mode="markers", name="SELL"))
fig.add_trace(go.Scatter(x=rev_df["Datetime"], y=rev_df["Close"], mode="markers", name="REVERSAL"))

st.plotly_chart(fig, use_container_width=True)
