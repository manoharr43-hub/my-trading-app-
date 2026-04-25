import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V8", layout="wide")
st_autorefresh(interval=60000, key="refresh")

st.title("🚀 NSE AI PRO V8 - SMART MONEY + MULTI TIMEFRAME")

# =============================
# STOCK LIST
# =============================
stocks = ["RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","ITC","LT"]

# =============================
# TIMEFRAMES
# =============================
timeframes = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m"
}

# =============================
# DATA LOADER
# =============================
@st.cache_data(ttl=300)
def load_data(stock, tf):
    return yf.Ticker(stock + ".NS").history(period="5d", interval=tf)

# =============================
# RSI
# =============================
def rsi(df, period=14):
    delta = df['Close'].diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / (loss + 1e-10)
    return 100 - (100 / (1 + rs))

# =============================
# SMART MONEY DETECTION
# =============================
def smart_money(df):
    volume_mean = df['Volume'].rolling(20).mean()
    last_vol = df['Volume'].iloc[-1]

    high = df['High'].rolling(20).max().iloc[-2]
    low = df['Low'].rolling(20).min().iloc[-2]
    price = df['Close'].iloc[-1]

    # 🔥 Volume trap logic
    if last_vol > volume_mean.iloc[-1] * 2:

        # breakout + fake move detection
        if price > high:
            return "⚠️ BUY TRAP (Distribution Risk)"
        elif price < low:
            return "⚠️ SELL TRAP (Accumulation Risk)"

        return "🔥 SMART MONEY ACTIVITY"

    return "NORMAL"

# =============================
# AI PREDICT
# =============================
def ai_predict(df):
    df = df.dropna()
    if len(df) < 30:
        return None

    df['Target'] = df['Close'].shift(-1)
    df.dropna(inplace=True)

    X = df[['Close','Volume']]
    y = df['Target']

    model = LinearRegression()
    model.fit(X, y)

    return model.predict(X.iloc[-1].values.reshape(1, -1))[0]

# =============================
# ANALYSIS ENGINE
# =============================
def analyze(df):

    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    pred = ai_predict(df)
    price = df['Close'].iloc[-1]

    signal = "WAIT"
    if pred:
        signal = "BUY" if pred > price else "SELL"

    r = rsi(df).iloc[-1]

    vol_ok = df['Volume'].iloc[-1] > df['Volume'].rolling(20).mean().iloc[-1]

    up = df['EMA20'].iloc[-1] > df['EMA50'].iloc[-1]
    down = df['EMA20'].iloc[-1] < df['EMA50'].iloc[-1]

    final = "WAIT"

    if signal == "BUY" and r < 70 and vol_ok and up:
        final = "STRONG BUY"

    elif signal == "SELL" and r > 30 and vol_ok and down:
        final = "STRONG SELL"

    return signal, round(r,2), final

# =============================
# ENTRY SYSTEM
# =============================
def entry_system(df):
    price = df['Close'].iloc[-1]
    atr = (df['High'] - df['Low']).rolling(14).mean().iloc[-1]

    sl = price - atr * 1.5
    tgt = price + atr * 3

    return round(sl,2), round(tgt,2)

# =============================
# CHART (SAFE)
# =============================
def show_chart(df, stock, tf):

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

    fig.update_layout(
        title=f"{stock} ({tf})",
        height=500
    )

    st.plotly_chart(fig, use_container_width=True, key=f"{stock}_{tf}")

# =============================
# UI - TIMEFRAME SELECT
# =============================
st.subheader("⏱ MULTI TIMEFRAME ANALYSIS")

selected_tf = st.selectbox("Select Timeframe", list(timeframes.keys()))

# =============================
# LIVE SCANNER
# =============================
st.subheader("📡 SMART MONEY SCANNER")

buy, sell = [], []

for s in stocks:

    df = load_data(s, timeframes[selected_tf])

    if df is None or len(df) < 50:
        continue

    signal, r, final = analyze(df)
    sm = smart_money(df)
    sl, tgt = entry_system(df)

    if final == "STRONG BUY":
        buy.append(s)
    elif final == "STRONG SELL":
        sell.append(s)

col1, col2 = st.columns(2)

with col1:
    st.success("🚀 BUY")
    st.write(buy)

with col2:
    st.error("💀 SELL")
    st.write(sell)

# =============================
# SINGLE CHART
# =============================
st.subheader("📊 CHART VIEW")

selected = st.selectbox("Select Stock", stocks)

df = load_data(selected, timeframes[selected_tf])

if df is not None:
    show_chart(df, selected, selected_tf)

# =============================
# SMART MONEY DETAILS
# =============================
st.subheader("🧠 SMART MONEY DETECTION")

df_sm = load_data(selected, timeframes[selected_tf])

if df_sm is not None:
    st.info(smart_money(df_sm))
