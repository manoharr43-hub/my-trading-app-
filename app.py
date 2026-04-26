import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="NSE AI PRO V23 FINAL", layout="wide")
st.title("🚀 NSE AI PRO V23 FINAL - Smart Money System")

st_autorefresh(interval=60000, key="refresh")

# =============================
# STOCK LIST
# =============================
stocks = [
    "HDFCBANK","ICICIBANK","SBIN","AXISBANK","KOTAKBANK",
    "INFY","TCS","HCLTECH","WIPRO",
    "RELIANCE","ONGC","TATASTEEL","HINDALCO"
]

# =============================
# SETTINGS
# =============================
st.sidebar.header("⚙️ Settings")
timeframe = st.sidebar.selectbox("Timeframe", ["5m","15m","30m"])
sl_pct = st.sidebar.slider("Stop Loss %", 0.5, 5.0, 1.0) / 100
tgt_pct = st.sidebar.slider("Target %", 1.0, 10.0, 2.0) / 100

# =============================
# SAFE DATA LOADER
# =============================
@st.cache_data(ttl=60)
def load_data(symbol, interval, period="5d"):
    try:
        df = yf.Ticker(symbol + ".NS").history(period=period, interval=interval)
        if df.empty:
            return pd.DataFrame()
        df = df.tz_localize(None)
        return df
    except:
        return pd.DataFrame()

# =============================
# INDICATORS
# =============================
def add_indicators(df):
    df = df.copy()

    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    tp = (df['High'] + df['Low'] + df['Close']) / 3

    # FIXED VWAP (NO ERROR)
    df['VWAP'] = (tp * df['Volume']).cumsum() / df['Volume'].cumsum()

    df['AvgVol'] = df['Volume'].rolling(20).mean()

    return df

# =============================
# HIGHER TIMEFRAME TREND
# =============================
def get_trend(symbol):
    df = load_data(symbol, "1h")
    if df.empty:
        return None

    df = add_indicators(df)
    last = df.iloc[-1]

    if last['EMA20'] > last['EMA50']:
        return "BULL"
    else:
        return "BEAR"

# =============================
# SIGNAL ENGINE
# =============================
def generate_signals(df, symbol):
    df = add_indicators(df)
    signals = []

    trend = get_trend(symbol)

    for i in range(30, len(df)):
        row = df.iloc[i]

        # volume filter
        if row['Volume'] < row['AvgVol'] * 2:
            continue

        price = round(row['Close'], 2)

        # BUY CONDITION
        if (
            price > row['VWAP'] and
            row['EMA20'] > row['EMA50'] and
            trend == "BULL"
        ):
            signals.append({
                "Stock": symbol,
                "Type": "BUY",
                "Entry": price,
                "SL": round(price * (1 - sl_pct), 2),
                "Target": round(price * (1 + tgt_pct), 2),
                "Time": df.index[i]
            })

        # SELL CONDITION
        elif (
            price < row['VWAP'] and
            row['EMA20'] < row['EMA50'] and
            trend == "BEAR"
        ):
            signals.append({
                "Stock": symbol,
                "Type": "SELL",
                "Entry": price,
                "SL": round(price * (1 + sl_pct), 2),
                "Target": round(price * (1 - tgt_pct), 2),
                "Time": df.index[i]
            })

    return signals, df

# =============================
# TRADE TRACKER
# =============================
def track_trades(signals, df):
    results = []

    for s in signals:
        status = "OPEN"

        for i in range(len(df)):
            high = df.iloc[i]["High"]
            low = df.iloc[i]["Low"]

            if s["Type"] == "BUY":
                if low <= s["SL"]:
                    status = "SL HIT"
                    break
                if high >= s["Target"]:
                    status
