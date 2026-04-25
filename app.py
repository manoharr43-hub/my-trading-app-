import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import datetime as dt
import plotly.graph_objects as go

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V23", layout="wide")

st.title("🚀 NSE AI PRO V23 - REAL INTRADAY PRO SYSTEM")

# =============================
# STOCK LIST
# =============================
stocks = ["RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","ITC"]

# =============================
# DATA LOADER (MULTI TF FIX)
# =============================
@st.cache_data(ttl=120)
def load_data(stock, interval):
    try:
        df = yf.Ticker(stock + ".NS").history(period="5d", interval=interval)
        if df is None or df.empty or len(df) < 20:
            return None
        return df
    except:
        return None

# =============================
# SMART MONEY CORE
# =============================
def analyze(df):

    if df is None or len(df) < 20:
        return "NO DATA", "NONE", "NONE", None

    df = df.dropna()

    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    price = df['Close'].iloc[-1]

    resistance = df['High'].rolling(20).max().iloc[-2]
    support = df['Low'].rolling(20).min().iloc[-2]

    vol_avg = df['Volume'].rolling(20).mean().iloc[-1]

    signal = "WAIT"
    breakout = "NONE"
    big = "NONE"
    time_sig = df.index[-1]

    # TREND FILTER
    trend_up = df['EMA20'].iloc[-1] > df['EMA50'].iloc[-1]

    # BREAKOUT LOGIC
    if price > resistance and trend_up:
        breakout = "BREAKOUT BUY"

    elif price < support and not trend_up:
        breakout = "BREAKOUT SELL"

    # SMART MONEY FILTER
    if df['Volume'].iloc[-1] > vol_avg * 1.7:

        if breakout == "BREAKOUT BUY":
            signal = "STRONG BUY"
            big = "INSTITUTION BUY"

        elif breakout == "BREAKOUT SELL":
            signal = "STRONG SELL"
            big = "INSTITUTION SELL"

    return signal, breakout, big, time_sig

# =============================
# MULTI TIMEFRAME ENGINE
# =============================
def multi_tf(stock):

    df1 = load_data(stock, "1m")
    df5 = load_data(stock, "5m")
    df15 = load_data(stock, "15m")
    df1h = load_data(stock, "60m")

    if df5 is None:
        return "NO DATA", "NONE", "NONE", None

    sig5, brk5, big5, t5 = analyze(df5)

    trend_ok = False

    if df15 is not None and df1h is not None:
        trend_ok = df15['Close'].iloc[-1] > df1h['Close'].iloc[-1]

    if sig5 == "STRONG BUY" and trend_ok:
        return "BUY", brk5, big5, t5

    if sig5 == "STRONG SELL" and not trend_ok:
        return "SELL", brk5, big5, t5

    return "WAIT", brk5, big5, t5

# =============================
# CHART (5M INTRADAY)
# =============================
def show_chart(stock):

    df = load_data(stock, "5m")

    if df is None:
        st.error("NO DATA")
        return

    signal, breakout, big, time_sig = multi_tf(stock)

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

    # SIGNAL MARKER
    fig.add_scatter(
        x=[df.index[-1]],
        y=[df['Close'].iloc[-1]],
        mode="markers+text",
        marker=dict(size=14),
        text=[signal]
    )

    st.subheader(f"📊 {stock} | {signal}")
    st.info(f"⏱ TIME: {time_sig}")
    st.info(f"📌 BREAKOUT: {breakout}")
    st.info(f"💰 SMART MONEY: {big}")

    st.plotly_chart(fig, use_container_width=True, key=stock)

# =============================
# SCANNER
# =============================
st.subheader("📡 INTRADAY SCANNER (V23 PRO)")

buy, sell = [], []

table = []

for s in stocks:

    signal, breakout, big, t = multi_tf(s)

    table.append({
        "Stock": s,
        "Signal": signal,
        "Breakout": breakout,
        "SmartMoney": big,
        "Time": str(t)
    })

    if signal == "BUY":
        buy.append(s)
    if signal == "SELL":
        sell.append(s)

st.dataframe(pd.DataFrame(table))

# =============================
# TOP LIST
# =============================
col1, col2 = st.columns(2)

with col1:
    st.success("🚀 BUY STOCKS")
    st.write(buy)

with col2:
    st.error("💀 SELL STOCKS")
    st.write(sell)

# =============================
# CHART VIEW
# =============================
st.subheader("📊 LIVE CHART")

selected = st.selectbox("Select Stock", stocks)

show_chart(selected)
