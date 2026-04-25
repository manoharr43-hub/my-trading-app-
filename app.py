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
st.set_page_config(page_title="🔥 NSE AI PRO V18", layout="wide")
st.title("🚀 NSE AI PRO V18 (FINAL STABLE)")
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
# STOCKS
# =============================
stocks = ["HDFCBANK","ICICIBANK","SBIN","RELIANCE","INFY","TCS","ITC","LT","AXISBANK","KOTAKBANK"]

# =============================
# FUNCTIONS
# =============================
def clean_time(ts):
    return pd.to_datetime(ts).strftime("%I:%M %p").lstrip("0")

@st.cache_data(ttl=60)
def load_data(stock, period="1d"):
    df = yf.Ticker(stock + ".NS").history(period=period, interval="5m")
    return df.between_time("09:15","15:30") if not df.empty else pd.DataFrame()

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
        buy = price > df['EMA20'].iloc[i] and price > df['VWAP'].iloc[i] and df['RSI'].iloc[i] > 52
        sell = price < df['EMA20'].iloc[i] and price < df['VWAP'].iloc[i] and df['RSI'].iloc[i] < 48

        if vol and buy and last_signal != "BUY":
            entries.append({"Stock":stock,"Type":"BIG BUY","Price":price,"TimeRaw":df.index[i],"Time":clean_time(df.index[i]),"Confidence":"MEDIUM"})
            last_signal = "BUY"

        elif vol and sell and last_signal != "SELL":
            entries.append({"Stock":stock,"Type":"BIG SELL","Price":price,"TimeRaw":df.index[i],"Time":clean_time(df.index[i]),"Confidence":"MEDIUM"})
            last_signal = "SELL"

    return entries[-10:]

# =============================
# LIVE
# =============================
if st.button("🔍 START LIVE"):
    all_big = []
    for s in stocks:
        df = load_data(s)
        all_big += big_player(df, s)
    st.session_state.live_big = sorted(all_big, key=lambda x: x["TimeRaw"])

# =============================
# LIVE DISPLAY
# =============================
if st.session_state.live_big:

    df_signals = pd.DataFrame(st.session_state.live_big)
    st.dataframe(df_signals)

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
                mode="markers",
                marker=dict(size=10, color="green" if row["Type"]=="BIG BUY" else "red")
            ))

        st.plotly_chart(fig, use_container_width=True)

# =============================
# BACKTEST (FINAL FIXED)
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

    # ===== ALWAYS SHOW CHART =====
    st.subheader("📊 Backtest Chart")

    stock_bt = st.selectbox("Select Stock", stocks, key="bt")

    df_chart_bt = yf.Ticker(stock_bt + ".NS").history(
        start=bt_date,
        end=bt_date + timedelta(days=1),
        interval="5m"
    )

    if not df_chart_bt.empty:

        df_chart_bt = df_chart_bt.between_time("09:15","15:30")

        fig_bt = go.Figure(data=[go.Candlestick(
            x=df_chart_bt.index,
            open=df_chart_bt['Open'],
            high=df_chart_bt['High'],
            low=df_chart_bt['Low'],
            close=df_chart_bt['Close']
        )])

        if not bt_df.empty:
            df_bt_stock = bt_df[bt_df["Stock"] == stock_bt]

            for _, row in df_bt_stock.iterrows():
                fig_bt.add_trace(go.Scatter(
                    x=[row["TimeRaw"]],
                    y=[row["Price"]],
                    mode="markers",
                    marker=dict(size=12, color="green" if row["Type"]=="BIG BUY" else "red")
                ))

        st.plotly_chart(fig_bt, use_container_width=True)

    else:
        st.error("No data for selected date")

    # ===== TABLE =====
    if not bt_df.empty:
        st.dataframe(bt_df)
    else:
        st.warning("No signals (chart still visible)")
