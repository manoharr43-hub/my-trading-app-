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
st.set_page_config(page_title="🔥 NSE AI PRO V13", layout="wide")
st.title("🚀 NSE AI PRO V13 (BACKTEST FOLDER + FINAL)")
st_autorefresh(interval=60000, key="refresh")

# =============================
# BACKTEST FOLDER SETUP
# =============================
BACKTEST_DIR = "backtests"
if not os.path.exists(BACKTEST_DIR):
    os.makedirs(BACKTEST_DIR)

# =============================
# SESSION INIT
# =============================
if "live_big" not in st.session_state:
    st.session_state.live_big = []
if "strength" not in st.session_state:
    st.session_state.strength = pd.DataFrame()
if "bt_df" not in st.session_state:
    st.session_state.bt_df = pd.DataFrame()

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
        if df.empty:
            return pd.DataFrame()
        return df.between_time("09:15","15:30").dropna()
    except:
        return pd.DataFrame()

# =============================
# BIG PLAYER LOGIC (NO DUPLICATE)
# =============================
def big_player(df, stock):
    if df.empty or len(df) < 30:
        return []

    df = df.copy()

    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    tp = (df['High'] + df['Low'] + df['Close']) / 3
    df['VWAP'] = (tp * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1)

    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / (avg_loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))

    df['AvgVol'] = df['Volume'].rolling(20).mean()

    df['Body'] = abs(df['Close'] - df['Open'])
    df['Range'] = df['High'] - df['Low']
    df['StrongCandle'] = df['Body'] > (df['Range'] * 0.6)

    entries = []
    last_signal = None

    for i in range(25, len(df)):
        price = df['Close'].iloc[i]

        score = 0
        if price > df['EMA20'].iloc[i]: score += 1
        if price > df['EMA50'].iloc[i]: score += 1
        if price > df['VWAP'].iloc[i]: score += 1
        if df['RSI'].iloc[i] > 60: score += 1
        if df['Volume'].iloc[i] > df['AvgVol'].iloc[i]*3: score += 1

        confidence = f"{score}/5"

        if (
            df['Volume'].iloc[i] > df['AvgVol'].iloc[i]*2.5 and
            price > df['EMA20'].iloc[i] > df['EMA50'].iloc[i] and
            price > df['VWAP'].iloc[i] and
            df['RSI'].iloc[i] > 55 and
            df['StrongCandle'].iloc[i]
        ):
            if last_signal != "BUY":
                entries.append({
                    "Stock": stock,
                    "Type": "BIG BUY",
                    "Price": round(price,2),
                    "TimeRaw": df.index[i],
                    "Time": clean_time(df.index[i]),
                    "Confidence": confidence
                })
                last_signal = "BUY"

        elif (
            df['Volume'].iloc[i] > df['AvgVol'].iloc[i]*2.5 and
            price < df['EMA20'].iloc[i] < df['EMA50'].iloc[i] and
            price < df['VWAP'].iloc[i] and
            df['RSI'].iloc[i] < 45 and
            df['StrongCandle'].iloc[i]
        ):
            if last_signal != "SELL":
                entries.append({
                    "Stock": stock,
                    "Type": "BIG SELL",
                    "Price": round(price,2),
                    "TimeRaw": df.index[i],
                    "Time": clean_time(df.index[i]),
                    "Confidence": confidence
                })
                last_signal = "SELL"

    return entries[-5:] if entries else []

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
                text=[f"{row['Type']} ({row['Confidence']})"],
                textposition="top center"
            ))

        st.plotly_chart(fig, use_container_width=True)

# =============================
# BACKTEST + SAVE
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

        if df.empty:
            continue

        bt_big += big_player(df, s)

    bt_df = pd.DataFrame(bt_big)

    if bt_df.empty:
        st.error("No Backtest Data")
    else:
        bt_df = bt_df.sort_values(by="TimeRaw")

        st.dataframe(bt_df[["Stock","Type","Price","Time","Confidence"]])

        # SAVE FILE
        file_path = f"{BACKTEST_DIR}/backtest_{bt_date}.csv"
        bt_df.to_csv(file_path, index=False)
        st.success(f"Saved: {file_path}")

# =============================
# BACKTEST FOLDER VIEW
# =============================
st.subheader("📂 BACKTEST FOLDER")

files = os.listdir(BACKTEST_DIR)

if files:
    selected_file = st.selectbox("Select File", files)
    df_saved = pd.read_csv(os.path.join(BACKTEST_DIR, selected_file))
    st.dataframe(df_saved)
else:
    st.info("No saved backtests yet")
