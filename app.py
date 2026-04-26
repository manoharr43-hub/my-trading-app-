import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import os

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO Intraday HQ", layout="wide")
st.title("🚀 NSE AI PRO – Intraday Sector HQ")

# =============================
# SECTOR MAP
# =============================
sector_map = {
    "Banking": ["HDFCBANK","ICICIBANK","SBIN","AXISBANK","KOTAKBANK"],
    "IT": ["INFY","TCS","HCLTECH","WIPRO","TECHM"],
    "Auto": ["M&M","TATAMOTORS","HEROMOTOCO","BAJAJ-AUTO","EICHERMOT"],
    "Pharma": ["SUNPHARMA","CIPLA","DIVISLAB","DRREDDY","AUROPHARMA"],
    "Metals": ["TATASTEEL","JSWSTEEL","HINDALCO","VEDL","SAIL"],
    "FMCG": ["HINDUNILVR","ITC","NESTLEIND","BRITANNIA","DABUR"],
    "Oil & Gas": ["RELIANCE","ONGC","BPCL","IOC","GAIL"],
    "Infra": ["L&T","ADANIPORTS","POWERGRID","NTPC","ULTRACEMCO"]
}

# =============================
# DATA LOADER
# =============================
@st.cache_data(ttl=120)
def load_data(stock, interval="5m", period="7d"):
    df = yf.download(stock+".NS", period=period, interval=interval, progress=False)
    df.dropna(inplace=True)
    df["EMA20"] = df["Close"].ewm(span=20).mean()
    df["EMA50"] = df["Close"].ewm(span=50).mean()
    df["VWAP"] = (df["Close"]*df["Volume"]).cumsum()/df["Volume"].cumsum()
    df["RSI"] = compute_rsi(df["Close"])
    return df

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain/avg_loss
    return 100 - (100/(1+rs))

# =============================
# SIGNALS
# =============================
def generate_signals(df):
    signals = []
    for i in range(1, len(df)):
        # Big Player Entry = sudden volume spike + price above EMA20
        if df["Volume"].iloc[i] > 1.5*df["Volume"].rolling(20).mean().iloc[i] and df["Close"].iloc[i] > df["EMA20"].iloc[i]:
            signals.append(("BIG PLAYER ENTRY", df.index[i], df["Close"].iloc[i]))

        # BUY Entry
        if df["EMA20"].iloc[i] > df["EMA50"].iloc[i] and df["RSI"].iloc[i] > 50:
            signals.append(("BUY ENTRY", df.index[i], df["Close"].iloc[i]))

        # SELL Entry
        if df["EMA20"].iloc[i] < df["EMA50"].iloc[i] and df["RSI"].iloc[i] < 50:
            signals.append(("SELL ENTRY", df.index[i], df["Close"].iloc[i]))

        # Exit Points (Target/Stop)
        if df["RSI"].iloc[i] > 70:
            signals.append(("EXIT TARGET", df.index[i], df["Close"].iloc[i]))
        elif df["RSI"].iloc[i] < 30:
            signals.append(("EXIT STOP", df.index[i], df["Close"].iloc[i]))

        # Reversal Detection
        if df["Close"].iloc[i] < df["VWAP"].iloc[i] and df["Close"].iloc[i-1] > df["VWAP"].iloc[i-1]:
            signals.append(("REVERSAL DOWN", df.index[i], df["Close"].iloc[i]))
        elif df["Close"].iloc[i] > df["VWAP"].iloc[i] and df["Close"].iloc[i-1] < df["VWAP"].iloc[i-1]:
            signals.append(("REVERSAL UP", df.index[i], df["Close"].iloc[i]))
    return signals

# =============================
# MAIN APP
# =============================
sector = st.sidebar.selectbox("Select Sector", list(sector_map.keys()))
stock = st.sidebar.selectbox("Select Stock", sector_map[sector])

df = load_data(stock)
signals = generate_signals(df)

# Show Table
st.subheader("📊 Intraday Signals")
sig_df = pd.DataFrame(signals, columns=["Signal","Time","Price"])
sig_df["Time"] = pd.to_datetime(sig_df["Time"])
sig_df["Time"] = sig_df["Time"].dt.strftime("%I:%M %p")
st.dataframe(sig_df)

# Show Chart
st.subheader("📈 Candlestick Chart + Indicators")
fig = go.Figure(data=[go.Candlestick(
    x=df.index, open=df["Open"], high=df["High"],
    low=df["Low"], close=df["Close"]
)])
fig.add_trace(go.Scatter(x=df.index, y=df["EMA20"], line=dict(color="blue"), name="EMA20"))
fig.add_trace(go.Scatter(x=df.index, y=df["EMA50"], line=dict(color="red"), name="EMA50"))
fig.add_trace(go.Scatter(x=df.index, y=df["VWAP"], line=dict(color="green"), name="VWAP"))
st.plotly_chart(fig, use_container_width=True)

# Save CSV Always
folder = "intraday_sector_csv"
os.makedirs(folder, exist_ok=True)
file_name = f"{stock}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
sig_df.to_csv(os.path.join(folder, file_name), index=False)

st.sidebar.subheader("📂 Saved Files")
for f in os.listdir(folder):
    st.sidebar.write(f)
