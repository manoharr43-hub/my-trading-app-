import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V6", layout="wide")

st.title("🚀 NSE AI PRO V6 (FIXED TIMING + BACKTEST CHART)")
st.markdown("---")

# =============================
# STOCK LIST
# =============================
sector_map = {
    "Banking": ["HDFCBANK","ICICIBANK","SBIN","AXISBANK","KOTAKBANK"],
    "IT": ["TCS","INFY","HCLTECH","WIPRO","TECHM"],
    "Pharma": ["SUNPHARMA","DRREDDY","CIPLA"],
    "Auto": ["MARUTI","M&M","TATAMOTORS"],
    "Metals": ["JSWSTEEL","TATASTEEL","HINDALCO"],
    "FMCG": ["ITC","RELIANCE","LT","BHARTIARTL"]
}

all_stocks = list(set(sum(sector_map.values(), [])))

# =============================
# TIME FORMAT (ORDER FIX)
# =============================
def clean_time(ts):
    return pd.to_datetime(ts).strftime("%I:%M %p")

# =============================
# DATA
# =============================
def load_data(stock):
    return yf.Ticker(stock + ".NS").history(period="1d", interval="5m")

# =============================
# BIG PLAYER
# =============================
def big_player(df, stock):
    df = df.copy()

    df['AvgVol'] = df['Volume'].rolling(20).mean()
    df['Spike'] = df['Volume'] > (df['AvgVol'] * 2)
    df['Move'] = df['Close'].diff()

    entries = []

    for i in range(len(df)):
        if df['Spike'].iloc[i] and df['Move'].iloc[i] > 0:
            entries.append({
                "Stock": stock,
                "Type": "BIG BUY",
                "Price": df['Close'].iloc[i],
                "Time": df.index[i]
            })

        elif df['Spike'].iloc[i] and df['Move'].iloc[i] < 0:
            entries.append({
                "Stock": stock,
                "Type": "BIG SELL",
                "Price": df['Close'].iloc[i],
                "Time": df.index[i]
            })

    # ✅ TIMING SERIAL FIX
    return sorted(entries, key=lambda x: x["Time"])

# =============================
# ANALYSIS
# =============================
def analyze(df):
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    signal = "BUY" if df['EMA20'].iloc[-1] > df['EMA50'].iloc[-1] else "SELL"

    return signal

# =============================
# LIVE RUN
# =============================
if st.button("🔍 START LIVE V6"):

    results = []
    big_entries = []

    for s in all_stocks:
        try:
            df = load_data(s)
            df = df.between_time("09:15","15:30")

            if len(df) < 50:
                continue

            signal = analyze(df)
            big = big_player(df, s)

            results.append({
                "Stock": s,
                "Signal": signal
            })

            big_entries += big

        except:
            pass

    st.session_state.live_res = results
    st.session_state.big_entries = big_entries

# =============================
# DISPLAY LIVE
# =============================
if "live_res" in st.session_state:

    st.subheader("📊 LIVE SIGNALS")
    st.dataframe(pd.DataFrame(st.session_state.live_res))

    st.subheader("🐋 BIG PLAYER (TIMING ORDER)")
    st.dataframe(pd.DataFrame(st.session_state.big_entries))

    # =============================
    # CHART
    # =============================
    stock = st.selectbox(
        "📈 Chart",
        pd.DataFrame(st.session_state.live_res)["Stock"].unique()
    )

    df_chart = load_data(stock)
    df_chart = df_chart.between_time("09:15","15:30")

    fig = go.Figure(data=[go.Candlestick(
        x=df_chart.index,
        open=df_chart['Open'],
        high=df_chart['High'],
        low=df_chart['Low'],
        close=df_chart['Close']
    )])

    # BIG PLAYER MARKERS
    df_big = pd.DataFrame(st.session_state.big_entries)

    if not df_big.empty:
        df_big = df_big[df_big["Stock"] == stock]

        for _, row in df_big.iterrows():
            fig.add_trace(go.Scatter(
                x=[row["Time"]],
                y=[row["Price"]],
                mode="markers+text",
                marker=dict(size=10, color="green" if row["Type"]=="BIG BUY" else "red"),
                text=[row["Type"]],
                textposition="top center"
            ))

    st.plotly_chart(fig, use_container_width=True)

# =============================
# BACKTEST (HIDDEN FIX)
# =============================
show_bt = st.checkbox("📊 Show Backtest (Optional)")

if show_bt:

    bt_date = st.date_input("Select Date", datetime.now().date() - timedelta(days=1))

    bt_res = []
    bt_big = []

    for s in all_stocks:
        try:
            df = yf.Ticker(s + ".NS").history(
                start=bt_date,
                end=bt_date + timedelta(days=1),
                interval="5m"
            )

            df = df.between_time("09:15","15:30")

            if len(df) < 50:
                continue

            signal = analyze(df)
            big = big_player(df, s)

            bt_res.append({"Stock": s, "Signal": signal})
            bt_big += big

        except:
            pass

    st.subheader("📊 BACKTEST RESULTS")
    st.dataframe(pd.DataFrame(bt_res))

    st.subheader("🐋 BACKTEST BIG PLAYER (SERIAL)")

    bt_big = sorted(bt_big, key=lambda x: x["Time"])
    st.dataframe(pd.DataFrame(bt_big))

    # =============================
    # BACKTEST CHART
    # =============================
    stock = st.selectbox("📉 Backtest Chart", pd.DataFrame(bt_res)["Stock"].unique())

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

    st.plotly_chart(fig, use_container_width=True)
