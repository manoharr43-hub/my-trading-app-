import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
import pytz
import time

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V22 FINAL", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone('Asia/Kolkata')
st.title("🚀 NSE AI PRO V22 - LIVE + BACKTEST + AI SIGNALS")
st.write(f"🕒 {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')}")

# =============================
# STOCK LIST
# =============================
stocks = [
    "HDFCBANK","ICICIBANK","SBIN","AXISBANK","KOTAKBANK",
    "TCS","INFY","WIPRO","HCLTECH","TECHM",
    "RELIANCE","ONGC","NTPC","POWERGRID","BPCL",
    "ITC","LT","TATASTEEL","BAJFINANCE","BHARTIARTL"
]

# =============================
# SAFE FETCH
# =============================
def get_data(stock, period="2d", interval="15m"):
    try:
        df = yf.Ticker(stock + ".NS").history(period=period, interval=interval)
        if df.empty:
            return None
        df.index = df.index.tz_convert(IST)
        return df
    except:
        return None

# =============================
# INDICATORS
# =============================
def indicators(df):
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1/14).mean()
    avg_loss = loss.ewm(alpha=1/14).mean()

    rs = avg_gain / (avg_loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))

    df['Vol_Avg'] = df['Volume'].rolling(20).mean()
    df['Big'] = df['Volume'] > df['Vol_Avg'] * 2

    return df

# =============================
# SIGNAL LOGIC
# =============================
def get_signal(df):
    last = df.iloc[-1]

    price = round(last['Close'], 2)

    signal = "WAIT"
    entry = sl = target = None

    # BUY
    if last['EMA20'] > last['EMA50'] and last['RSI'] > 55:
        signal = "STRONG BUY"
        entry = price
        sl = round(price * 0.99, 2)
        target = round(price * 1.02, 2)

    # SELL
    elif last['EMA20'] < last['EMA50'] and last['RSI'] < 45:
        signal = "STRONG SELL"
        entry = price
        sl = round(price * 1.01, 2)
        target = round(price * 0.98, 2)

    # REVERSAL
    elif last['RSI'] < 30:
        signal = "REVERSAL BUY"
        entry = price
        sl = round(price * 0.98, 2)
        target = round(price * 1.03, 2)

    big_player = "YES" if last['Big'] else "NO"

    return signal, entry, sl, target, big_player

# =============================
# TABS
# =============================
tab1, tab2, tab3 = st.tabs(["🔍 LIVE SCANNER", "📊 BACKTEST", "📈 CHART"])

# =============================
# LIVE SCANNER
# =============================
with tab1:
    if st.button("🚀 SCAN MARKET"):
        results = []

        for s in stocks:
            df = get_data(s)
            if df is None:
                continue

            df
