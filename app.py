import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
import os

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V15", layout="wide")
st.title("🚀 NSE AI PRO V15 (FINAL STABLE)")
st_autorefresh(interval=60000, key="refresh")

# =============================
# BACKTEST FOLDER
# =============================
BACKTEST_DIR = "backtests"
os.makedirs(BACKTEST_DIR, exist_ok=True)

# =============================
# SESSION
# =============================
if "live_big" not in st.session_state:
    st.session_state.live_big = []
if "strength" not in st.session_state:
    st.session_state.strength = pd.DataFrame()

# =============================
# STOCKS (ALL SECTORS)
# =============================
stocks = [
    "HDFCBANK","ICICIBANK","SBIN","AXISBANK","KOTAKBANK","INDUSINDBK",
    "INFY","TCS","WIPRO","HCLTECH","TECHM",
    "ITC","HINDUNILVR","NESTLEIND","BRITANNIA","DABUR",
    "RELIANCE","ONGC","BPCL","IOC","GAIL",
    "TATAMOTORS","MARUTI","M&M","BAJAJ-AUTO","HEROMOTOCO",
    "SUNPHARMA","DRREDDY","CIPLA","DIVISLAB","LUPIN",
    "TATASTEEL","JSWSTEEL","HINDALCO","COALINDIA",
    "LT","ULTRACEMCO","GRASIM","ADANIENT","ADANIPORTS"
]

# =============================
# FUNCTIONS
# =============================
def clean_time(ts):
    try:
        return pd.to_datetime(ts).strftime("%I:%M %p").lstrip("0")
    except:
        return ""

@st.cache_data(ttl=60)
def load_data(stock, period="1d"):
    try:
        df = yf.Ticker(stock + ".NS").history(period=period, interval="5m")
        return df.between_time("09:15","15:30").dropna()
    except:
        return pd.DataFrame()

# =============================
# BIG PLAYER LOGIC (IMPROVED)
# =============================
def big_player(df, stock):
    if df.empty or len(df) < 30:
        return []

    df = df.copy()

    df['EMA20'] = df['Close'].ewm(span=20).mean()
    tp = (df['High'] + df['Low'] + df['Close']) / 3
    df['VWAP'] = (tp * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1)

    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    rs = gain.rolling(14).mean() / (loss.rolling(14).mean() + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))

    df['AvgVol'] = df['Volume'].rolling(20).mean()

    entries = []
    last_signal = None

    for i in range(25, len(df)):
        price = df['Close'].iloc[i]

        vol = df['Volume'].iloc[i] > df['AvgVol'].iloc[i] * 1.5
        buy_cond = price > df['EMA20'].iloc[i] and price > df['VWAP'].iloc[i] and df['RSI'].iloc[i] > 52
        sell_cond = price < df['EMA20'].iloc[i] and price < df['VWAP'].iloc[i] and df['RSI'].iloc[i] < 48

        if vol and buy_cond:
            if last_signal != "BUY":
                entries.append({
                    "Stock": stock,
                    "Type": "BIG BUY",
                    "Price": round(price,2),
                    "TimeRaw": df.index[i],
                    "Time": clean_time(df.index[i]),
                    "Confidence": "MEDIUM"
                })
                last_signal = "BUY"

        elif vol and sell_cond:
            if last_signal != "SELL":
                entries.append({
                    "Stock": stock,
                    "Type": "BIG SELL",
                    "Price": round(price,2),
                    "TimeRaw": df.index[i],
                    "Time": clean_time(df.index[i]),
                    "Confidence": "MEDIUM"
                })
                last_signal = "SELL"

    return entries[-10:]

def strength_meter(df):
    if df.empty:
        return 0
    return round(((df['Close'].iloc[-1] / df['Close'].iloc[0]) - 1) * 100, 2)

# =============================
# LIVE
# =============================
if st.button("🔍 START LIVE"):
    all_big, strength_data = [], []

    for s in stocks:
        df = load_data(s)
        if df.empty:
            continue

        all_big += big_player(df, s)
        strength_data.append({"Stock": s, "Strength %": strength_meter(df)})

    st.session_state.live_big = sorted(all_big, key=lambda x: x["TimeRaw"])
    st.session_state.strength = pd.DataFrame(strength_data).sort_values(by="Strength %", ascending=False)

# =============================
# DISPLAY LIVE
# =============================
if st.session_state.live_big:

    df_signals = pd.DataFrame(st.session_state.live_big)

    st.subheader("🐋 BIG PLAYER SIGNALS")
    st.dataframe(df_signals.sort_values(by="TimeRaw", ascending=False), use_container_width=True)

    stock = st.selectbox("📈 Chart", stocks)

    df_chart = load_data(stock)

    if not df_chart.empty:
        fig = go.Figure(data=[go.Candlestick(
            x=df_chart.index,
            open=df_chart['Open'],
            high=df_chart['High'],
            low=df_chart['Low'],
            close=df_chart['Close']
        )])

        df_big = df_signals[df_signals["Stock"] == stock]

        for _, row in df_big.iterrows():
            fig.add_trace(go.Scatter(
                x=[row["TimeRaw"]],
                y=[row["Price"]],
                mode="markers+text",
                marker=dict(size=10, color="green" if row["Type"]=="BIG BUY" else "red"),
                text=[row["Type"]],
                textposition="top center"
            ))

        st.plotly_chart(fig, use_container_width=True)

# =============================
# BACKTEST
# =============================
if st.checkbox("📊 Enable Backtest"):

    bt_date = st.date_input("Select Date", datetime.now().date() - timedelta(days=1))

    bt_big = []

    for s in stocks:
        df = yf.Ticker(s + ".NS").history(
            start=bt_date,
            end=bt_date + timedelta(days=1),
            interval="5m"
        )

        if df.empty:
            continue

        df = df.between_time("09:15","15:30")

        bt_big += big_player(df, s)

    bt_df = pd.DataFrame(bt_big)

    if not bt_df.empty:
        st.dataframe(bt_df)

        file_path = f"{BACKTEST_DIR}/bt_{bt_date}.csv"
        bt_df.to_csv(file_path, index=False)
        st.success(f"Saved: {file_path}")
    else:
        st.warning("No Backtest Data")

# =============================
# BACKTEST FOLDER VIEW
# =============================
st.subheader("📂 BACKTEST FILES")

files = os.listdir(BACKTEST_DIR)

if files:
    f = st.selectbox("Select File", files)
    df_saved = pd.read_csv(os.path.join(BACKTEST_DIR, f))
    st.dataframe(df_saved)
else:
    st.info("No files yet")
