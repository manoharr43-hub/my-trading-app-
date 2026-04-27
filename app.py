import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
import pytz

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V10", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone('Asia/Kolkata')
st.title("🚀 NSE AI PRO V10 - SMART MONEY SYSTEM")

# =============================
# STOCK LIST
# =============================
stocks = ["HDFCBANK","ICICIBANK","SBIN","RELIANCE","TCS","INFY","ITC","LT","BHARTIARTL"]

# =============================
# DATA FETCH (FASTER)
# =============================
@st.cache_data(ttl=60)
def get_data(stock, period="5d", interval="15m"):
    try:
        df = yf.download(stock + ".NS", period=period, interval=interval, progress=False)
        return df.dropna() if df is not None and not df.empty else None
    except:
        return None

# =============================
# INDICATORS
# =============================
def add_indicators(df):
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    # RSI
    delta = df['Close'].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100/(1+rs))

    # VWAP
    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()

    # MACD
    exp1 = df['Close'].ewm(span=12).mean()
    exp2 = df['Close'].ewm(span=26).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9).mean()

    # ATR (for SL/Target)
    df['TR'] = np.maximum(df['High']-df['Low'], 
                np.maximum(abs(df['High']-df['Close'].shift()), abs(df['Low']-df['Close'].shift())))
    df['ATR'] = df['TR'].rolling(14).mean()

    return df

# =============================
# AI SCORE (IMPROVED)
# =============================
def ai_score(df):
    last = df.iloc[-1]
    score = 0

    if last['EMA20'] > last['EMA50']: score += 25
    if 45 < last['RSI'] < 65: score += 15
    if last['Close'] > last['VWAP']: score += 20
    if last['MACD'] > last['Signal']: score += 20
    if last['Volume'] > df['Volume'].rolling(20).mean().iloc[-1]: score += 20

    return score

# =============================
# SIGNAL
# =============================
def get_signal(score):
    if score >= 80:
        return "🚀 STRONG BUY"
    elif score <= 30:
        return "💀 STRONG SELL"
    elif score >= 60:
        return "BUY"
    elif score <= 40:
        return "SELL"
    else:
        return "WAIT"

# =============================
# BIG PLAYER DETECTION
# =============================
def big_player(df):
    last = df.iloc[-1]
    avg_vol = df['Volume'].rolling(20).mean().iloc[-1]
    if last['Volume'] > avg_vol * 3:
        return "🐋 BIG ENTRY"
    return "-"

# =============================
# LIVE SCANNER
# =============================
if st.button("🔍 LIVE SCAN"):
    data = []

    for s in stocks:
        df = get_data(s)
        if df is None or len(df) < 50:
            continue

        df = add_indicators(df)
        last = df.iloc[-1]

        score = ai_score(df)
        signal = get_signal(score)
        alert = big_player(df)

        price = round(last['Close'], 2)
        atr = last['ATR']

        # SL/Target
        if "BUY" in signal:
            sl = round(price - atr, 2)
            tgt = round(price + atr*2, 2)
        elif "SELL" in signal:
            sl = round(price + atr, 2)
            tgt = round(price - atr*2, 2)
        else:
            sl = tgt = 0

        time = df.index[-1].tz_localize(None)

        data.append({
            "Stock": s,
            "Price": price,
            "Signal": signal,
            "Score": score,
            "Big Player": alert,
            "SL": sl,
            "Target": tgt,
            "Time": time
        })

    st.dataframe(pd.DataFrame(data), use_container_width=True)

# =============================
# BACKTEST (IMPROVED)
# =============================
if st.button("📊 BACKTEST"):
    logs = []

    for s in stocks:
        df = get_data(s, period="1mo")
        if df is None or len(df) < 100:
            continue

        df = add_indicators(df)

        for i in range(50, len(df)):
            temp = df.iloc[:i+1]
            score = ai_score(temp)

            if score >= 80:
                logs.append({
                    "Stock": s,
                    "Time": df.index[i],
                    "Price": round(df.iloc[i]['Close'],2),
                    "Signal": "BUY"
                })

    st.dataframe(pd.DataFrame(logs), use_container_width=True)

# =============================
# CHART
# =============================
st.markdown("---")
stock = st.selectbox("Select Stock", stocks)
df = get_data(stock)

if df is not None:
    df = add_indicators(df)

    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close']
    ))

    fig.add_trace(go.Scatter(x=df.index, y=df['VWAP'], name="VWAP"))

    st.plotly_chart(fig, use_container_width=True)
