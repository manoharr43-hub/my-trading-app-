import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V4", layout="wide")
st_autorefresh(interval=60000, key="refresh")

st.title("🚀 NSE AI PRO DASHBOARD V4")
st.markdown("---")

# =============================
# STOCK LIST
# =============================
stocks = [
    "RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","ITC","LT",
    "AXISBANK","BHARTIARTL","KOTAKBANK","MARUTI","M&M","TATAMOTORS",
    "SUNPHARMA","DRREDDY","CIPLA","HCLTECH","WIPRO","TECHM",
    "JSWSTEEL","TATASTEEL","HINDALCO"
]

# =============================
# AI SCORE ENGINE
# =============================
def ai_score(df):
    score = 0
    close = df['Close']

    ema20 = close.ewm(span=20).mean()
    ema50 = close.ewm(span=50).mean()

    if ema20.iloc[-1] > ema50.iloc[-1]:
        score += 30
    else:
        score += 10

    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    if rsi.iloc[-1] < 60:
        score += 30
    else:
        score += 10

    if df['Volume'].iloc[-1] > df['Volume'].rolling(20).mean().iloc[-1]:
        score += 40
    else:
        score += 10

    return min(score, 100)

# =============================
# SIGNAL ENGINE
# =============================
def signal_engine(df):
    close = df['Close']

    ema20 = close.ewm(span=20).mean()
    ema50 = close.ewm(span=50).mean()

    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    if ema20.iloc[-1] > ema50.iloc[-1] and rsi.iloc[-1] < 65:
        return "🚀 BUY"
    elif ema20.iloc[-1] < ema50.iloc[-1] and rsi.iloc[-1] > 35:
        return "💀 SELL"
    else:
        return "WAIT"

# =============================
# LEVELS
# =============================
def levels(price):
    return price, price*0.98, price*1.03, price*1.06

# =============================
# CHART (FIXED CLARITY)
# =============================
def show_chart(df, stock):

    df = df.dropna()

    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        increasing_line_color='green',
        decreasing_line_color='red'
    ))

    fig.update_layout(
        title=f"{stock} CHART",
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)

# =============================
# BACKTEST (FIXED DATE)
# =============================
def backtest(stock, date):

    start = pd.to_datetime(date)
    end = start + pd.Timedelta(days=1)

    df = yf.Ticker(stock+".NS").history(
        start=start,
        end=end,
        interval="15m"
    )

    df
