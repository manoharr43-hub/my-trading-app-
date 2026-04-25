import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from streamlit_autorefresh import st_autorefresh
import plotly.graph_objects as go

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V11", layout="wide")
st_autorefresh(interval=60000, key="refresh")

st.title("🚀 NSE AI PRO V11 - SMART MONEY + MULTI TF")

# =============================
# STOCKS
# =============================
stocks = ["RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","ITC"]

# =============================
# TIMEFRAMES
# =============================
timeframes = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "1H": "60m"
}

# =============================
# DATA LOADER
# =============================
@st.cache_data(ttl=300)
def load_data(stock, tf):
    return yf.Ticker(stock + ".NS").history(period="5d", interval=tf)

# =============================
# SMART MONEY DETECTION
# =============================
def smart_money(df):

    vol_avg = df['Volume'].rolling(20).mean()
    last_vol = df['Volume'].iloc[-1]

    resistance = df['High'].rolling(20).max().iloc[-2]
    support = df['Low'].rolling(20).min().iloc[-2]

    price = df['Close'].iloc[-1]

    signal = "NORMAL"

    # 🔥 Volume Trap
    if last_vol > vol_avg.iloc[-1] * 2:

        if price > resistance:
            signal = "⚠️ DISTRIBUTION (BUY TRAP)"
        elif price < support:
            signal = "⚠️ ACCUMULATION (SELL TRAP)"
        else:
            signal = "🔥 SMART MONEY ACTIVE"

    return signal

# =============================
# TREND ANALYSIS
# =============================
def trend(df):

    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    if df['EMA20'].iloc[-1] > df['EMA50'].iloc[-1]:
        return "UPTREND"
    else:
        return "DOWNTREND"

# =============================
# SIGNAL ENGINE
# =============================
def signal_engine(df):

    price = df['Close'].iloc[-1]

    resistance = df['High'].rolling(20).max().iloc[-2]
    support = df['Low'].rolling(20).min().iloc[-2]

    vol_spike = df['Volume'].iloc[-1] > df['Volume'].rolling(20).mean().iloc[-1] * 1.8

    breakout = None
    big_entry = None

    if price > resistance:
        breakout = "UP BREAKOUT"
    elif price < support:
        breakout = "DOWN BREAKOUT"

    if breakout == "UP BREAKOUT" and vol_spike:
        big_entry = "BIG BUY ENTRY"

    if breakout == "DOWN BREAKOUT" and vol_spike:
        big_entry = "BIG SELL ENTRY"

    return breakout, big_entry

# =============================
# CHART
# =============================
def show_chart(df, stock, tf):

    breakout, big_entry = signal_engine(df)
    sm = smart_money(df)
    tr = trend(df)

    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close']
    ))

    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['Close'].ewm(span=20).mean(),
        name="EMA20"
    ))

    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['Close'].ewm(span=50).mean(),
        name="EMA50"
    ))

    # BUY/SELL BASED ON TREND
    if tr == "UPTREND":
        st.success("📈 TREND: UP")
    else:
        st.error("📉 TREND: DOWN")

    # BREAKOUT MARKER
    if breakout:
        fig.add_scatter(
            x=[df.index[-1]],
            y=[df['Close'].iloc[-1]],
            mode="markers+text",
            marker=dict(size=12, color="blue"),
            text=[breakout],
            textposition="bottom center"
        )

    # BIG ENTRY MARKER
    if big_entry:
        color = "green" if "BUY" in big_entry else "red"

        fig.add_scatter(
            x=[df.index[-1]],
            y=[df['Close'].iloc[-1]],
            mode="markers+text",
            marker=dict(size=14, color=color),
            text=[big_entry],
            textposition="top center"
        )

    fig.update_layout(title=f"{stock} ({tf}) | SMART MONEY", height=550)

    st.plotly_chart(fig, use_container_width=True, key=f"{stock}_{tf}")

# =============================
# UI
# =============================
st.subheader("⏱ MULTI TIMEFRAME ANALYSIS")

selected_tf = st.selectbox("Select Timeframe", list(timeframes.keys()))

selected_stock = st.selectbox("Select Stock", stocks)

df = load_data(selected_stock, timeframes[selected_tf])

if df is not None and len(df) > 50:

    st.subheader("🧠 SMART MONEY STATUS")
    st.info(smart_money(df))

    show_chart(df, selected_stock, selected_tf)

# =============================
# SCANNER (MULTI TF CONFIRMATION)
# =============================
st.subheader("🔥 SMART MONEY SCANNER")

buy, sell = [], []

for s in stocks:

    df_5m = load_data(s, "5m")
    df_15m = load_data(s, "15m")

    if df_5m is None or df_15m is None:
        continue

    breakout, big_entry = signal_engine(df_5m)
    trend_15 = trend(df_15m)

    if big_entry == "BIG BUY ENTRY" and trend_15 == "UPTREND":
        buy.append(s)

    if big_entry == "BIG SELL ENTRY" and trend_15 == "DOWNTREND":
        sell.append(s)

col1, col2 = st.columns(2)

with col1:
    st.success("🚀 STRONG BUY (SMART MONEY CONFIRMED)")
    st.write(buy)

with col2:
    st.error("💀 STRONG SELL (SMART MONEY CONFIRMED)")
    st.write(sell)
