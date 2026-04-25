import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V7", layout="wide")

st.title("🚀 NSE AI PRO V7 (FINAL FIXED)")
st.markdown("---")

# =============================
# STOCKS
# =============================
stocks = ["HDFCBANK","ICICIBANK","SBIN","TCS","INFY","RELIANCE","ITC","LT"]

# =============================
# TIME FORMAT
# =============================
def clean_time(ts):
    return pd.to_datetime(ts).strftime("%I:%M %p").lstrip("0")

# =============================
# DATA
# =============================
def load_data(stock, period="1d"):
    return yf.Ticker(stock + ".NS").history(period=period, interval="5m")

# =============================
# BIG PLAYER DETECTION
# =============================
def big_player(df, stock):
    df = df.copy()

    df['AvgVol'] = df['Volume'].rolling(20).mean()
    df['Spike'] = df['Volume'] > df['AvgVol'] * 2
    df['Move'] = df['Close'].diff()

    entries = []

    for i in range(len(df)):
        if df['Spike'].iloc[i] and df['Move'].iloc[i] > 0:
            entries.append({
                "Stock": stock,
                "Type": "BIG BUY",
                "Price": df['Close'].iloc[i],
                "TimeRaw": df.index[i],
                "Time": clean_time(df.index[i])
            })

        elif df['Spike'].iloc[i] and df['Move'].iloc[i] < 0:
            entries.append({
                "Stock": stock,
                "Type": "BIG SELL",
                "Price": df['Close'].iloc[i],
                "TimeRaw": df.index[i],
                "Time": clean_time(df.index[i])
            })

    # SERIAL ORDER FIX
    entries = sorted(entries, key=lambda x: x["TimeRaw"])

    return entries

# =============================
# LIVE
# =============================
if st.button("🔍 START LIVE"):

    all_big = []

    for s in stocks:
        try:
            df = load_data(s)
            df = df.between_time("09:15","15:30")

            big = big_player(df, s)
            all_big += big

        except:
            pass

    st.session_state.live_big = all_big

# =============================
# LIVE DISPLAY
# =============================
if "live_big" in st.session_state:

    st.subheader("🐋 BIG PLAYER (LIVE SERIAL)")
    st.dataframe(pd.DataFrame(st.session_state.live_big)[["Stock","Type","Price","Time"]])

    # CHART
    stock = st.selectbox("📈 Chart", stocks)

    df_chart = load_data(stock)
    df_chart = df_chart.between_time("09:15","15:30")

    fig = go.Figure(data=[go.Candlestick(
        x=df_chart.index,
        open=df_chart['Open'],
        high=df_chart['High'],
        low=df_chart['Low'],
        close=df_chart['Close']
    )])

    df_big = pd.DataFrame(st.session_state.live_big)
    df_big = df_big[df_big["Stock"] == stock]

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

    bt_date = st.date_input("Select Date", datetime.now().date()-timedelta(days=1))

    bt_big = []

    for s in stocks:
        try:
            df = yf.Ticker(s + ".NS").history(
                start=bt_date,
                end=bt_date + timedelta(days=1),
                interval="5m"
            )

            df = df.between_time("09:15","15:30")

            big = big_player(df, s)
            bt_big += big

        except:
            pass

    # SERIAL FIX
    bt_big = sorted(bt_big, key=lambda x: x["TimeRaw"])

    st.subheader("🐋 BACKTEST BIG PLAYER")
    st.dataframe(pd.DataFrame(bt_big)[["Stock","Type","Price","Time"]])

    # BACKTEST CHART
    stock = st.selectbox("📉 Backtest Chart", stocks)

    df_chart = yf.Ticker(stock + ".NS").history(
        start=bt_date,
        end=bt_date + timedelta(days=1),
        interval="5m"
    )

    df_chart = df_chart.between_time("09:15","15:30")

    fig = go.Figure(data=[go.Candlestick(
        x=df_chart.index,
        open=df_chart['Open'],
        high=df_chart['High'],
        low=df_chart['Low'],
        close=df_chart['Close']
    )])

    df_bt = pd.DataFrame(bt_big)
    df_bt = df_bt[df_bt["Stock"] == stock]

    for _, row in df_bt.iterrows():
        fig.add_trace(go.Scatter(
            x=[row["TimeRaw"]],
            y=[row["Price"]],
            mode="markers+text",
            marker=dict(size=12, color="green" if row["Type"]=="BIG BUY" else "red"),
            text=[row["Type"]],
            textposition="top center"
        ))

    st.plotly_chart(fig, use_container_width=True)
