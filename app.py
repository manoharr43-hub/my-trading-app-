import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import os

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO Intraday HQ", layout="wide")
st.title("🚀 NSE AI PRO – Intraday HQ")

# Auto Refresh every 3 minutes
st_autorefresh(interval=180000, key="refresh")

# =============================
# DATA LOADER
# =============================
@st.cache_data(ttl=120)
def load_data(stock, interval="5m", period="7d"):
    try:
        df = yf.download(stock+".NS", period=period, interval=interval, progress=False)
        df.dropna(inplace=True)
        df["EMA20"] = df["Close"].ewm(span=20).mean()
        df["EMA50"] = df["Close"].ewm(span=50).mean()
        return df
    except Exception as e:
        st.error(f"Data load error: {e}")
        return pd.DataFrame()

# =============================
# SIGNALS
# =============================
def generate_signals(df):
    signals = []
    for i in range(1, len(df)):
        if df["EMA20"].iloc[i] > df["EMA50"].iloc[i] and df["EMA20"].iloc[i-1] <= df["EMA50"].iloc[i-1]:
            signals.append(("BUY", df.index[i], df["Close"].iloc[i]))
        elif df["EMA20"].iloc[i] < df["EMA50"].iloc[i] and df["EMA20"].iloc[i-1] >= df["EMA50"].iloc[i-1]:
            signals.append(("SELL", df.index[i], df["Close"].iloc[i]))
    return signals

# =============================
# MAIN APP
# =============================
stock = st.sidebar.text_input("Enter Stock Symbol (e.g., INFY)", "INFY")
df = load_data(stock)

if not df.empty:
    signals = generate_signals(df)

    # Show Table
    st.subheader("📊 Intraday Signals")
    sig_df = pd.DataFrame(signals, columns=["Signal","Time","Price"])
    sig_df["Time"] = sig_df["Time"].strftime("%I:%M %p")  # Clean Time Format
    st.dataframe(sig_df)

    # Show Chart
    st.subheader("📈 Candlestick Chart with EMA")
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"]
    )])
    fig.add_trace(go.Scatter(x=df.index, y=df["EMA20"], line=dict(color="blue"), name="EMA20"))
    fig.add_trace(go.Scatter(x=df.index, y=df["EMA50"], line=dict(color="red"), name="EMA50"))
    st.plotly_chart(fig, use_container_width=True)

    # Save CSV Always
    folder = "intraday_csv"
    os.makedirs(folder, exist_ok=True)
    file_name = f"{stock}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    sig_df.to_csv(os.path.join(folder, file_name), index=False)

    st.sidebar.subheader("📂 Saved Files")
    for f in os.listdir(folder):
        st.sidebar.write(f)
else:
    st.warning("No data available. Please check stock symbol.")
