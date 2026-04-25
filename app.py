import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V9.2", layout="wide")
st.title("🚀 NSE AI PRO V9.2 (FINAL STABLE)")
st.markdown("---")

# =============================
# SAFE SESSION INIT
# =============================
if "live_big" not in st.session_state:
    st.session_state.live_big = []

if "strength" not in st.session_state:
    st.session_state.strength = pd.DataFrame()

# =============================
# SECTOR STOCK LIST
# =============================
BANKING = ["HDFCBANK","ICICIBANK","SBIN","KOTAKBANK","AXISBANK","INDUSINDBK","BANKBARODA","PNB"]
IT = ["TCS","INFY","WIPRO","HCLTECH","TECHM","LTIM","PERSISTENT"]
OIL = ["RELIANCE","ONGC","IOC","BPCL","HPCL"]
AUTO = ["MARUTI","TATAMOTORS","M&M","HEROMOTOCO","BAJAJ-AUTO"]
INFRA = ["LT","ULTRACEMCO","JSWSTEEL","TATASTEEL","HINDALCO"]
PHARMA = ["SUNPHARMA","DRREDDY","CIPLA","DIVISLAB"]
FMCG = ["HINDUNILVR","ITC","NESTLEIND","BRITANNIA"]

sector_map = {
    "ALL": list(set(BANKING + IT + OIL + AUTO + INFRA + PHARMA + FMCG)),
    "BANKING": BANKING,
    "IT": IT,
    "OIL": OIL,
    "AUTO": AUTO,
    "INFRA": INFRA,
    "PHARMA": PHARMA,
    "FMCG": FMCG
}

selected_sector = st.selectbox("📊 Select Sector", sector_map.keys())
stocks = sector_map[selected_sector]

# =============================
# TIME FORMAT
# =============================
def clean_time(ts):
    return pd.to_datetime(ts).strftime("%I:%M %p").lstrip("0")

# =============================
# LOAD DATA
# =============================
@st.cache_data(ttl=60)
def load_data(stock, period="1d"):
    df = yf.Ticker(stock + ".NS").history(period=period, interval="5m")
    if df.empty:
        return pd.DataFrame()
    return df.between_time("09:15","15:30")

# =============================
# BIG PLAYER LOGIC
# =============================
def big_player(df, stock):
    if df.empty or len(df) < 25:
        return []

    df = df.copy()
    df['AvgVol'] = df['Volume'].rolling(20).mean()
    df['Spike'] = df['Volume'] > df['AvgVol'] * 2
    df['Move'] = df['Close'].diff()
    df['EMA20'] = df['Close'].ewm(span=20).mean()

    entries = []

    for i in range(20, len(df)):
        price = df['Close'].iloc[i]
        ema = df['EMA20'].iloc[i]

        if df['Spike'].iloc[i] and df['Move'].iloc[i] > 0 and price > ema:
            entries.append({
                "Stock": stock,
                "Type": "BIG BUY",
                "Price": price,
                "TimeRaw": df.index[i],
                "Time": clean_time(df.index[i])
            })

        elif df['Spike'].iloc[i] and df['Move'].iloc[i] < 0 and price < ema:
            entries.append({
                "Stock": stock,
                "Type": "BIG SELL",
                "Price": price,
                "TimeRaw": df.index[i],
                "Time": clean_time(df.index[i])
            })

    return entries

# =============================
# STRENGTH
# =============================
def strength_meter(df):
    if df.empty:
        return 0
    return (df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0]

# =============================
# LIVE
# =============================
if st.button("🔍 START LIVE"):

    all_big = []
    strength_data = []

    for s in stocks:
        try:
            df = load_data(s)

            if df.empty:
                continue

            all_big += big_player(df, s)

            strength_data.append({
                "Stock": s,
                "Strength": strength_meter(df)
            })

        except:
            pass

    all_big = sorted(all_big, key=lambda x: x["TimeRaw"])
    strength_df = pd.DataFrame(strength_data).sort_values(by="Strength", ascending=False)

    st.session_state.live_big = all_big
    st.session_state.strength = strength_df

# =============================
# LIVE DISPLAY
# =============================
if len(st.session_state.live_big) > 0:

    st.subheader("🐋 BIG PLAYER")
    st.dataframe(pd.DataFrame(st.session_state.live_big)[["Stock","Type","Price","Time"]])

    if not st.session_state.strength.empty:
        st.subheader("🔥 STRONG STOCKS")
        st.dataframe(st.session_state.strength.head(5))

        st.subheader("❄️ WEAK STOCKS")
        st.dataframe(st.session_state.strength.tail(5))

    # CHART
    stock = st.selectbox("📈 Chart", stocks)

    df_chart = load_data(stock)

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
            marker=dict(
                size=10,
                color="green" if row["Type"] == "BIG BUY" else "red"
            ),
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
        try:
            df = yf.Ticker(s + ".NS").history(
                start=bt_date,
                end=bt_date + timedelta(days=1),
                interval="5m"
            )

            df = df.between_time("09:15", "15:30")

            if df.empty:
                continue

            bt_big += big_player(df, s)

        except:
            pass

    bt_big = sorted(bt_big, key=lambda x: x["TimeRaw"])

    if len(bt_big) > 0:
        st.subheader("🐋 BACKTEST BIG PLAYER")
        st.dataframe(pd.DataFrame(bt_big)[["Stock","Type","Price","Time"]])

    # BACKTEST CHART
    stock = st.selectbox("📉 Backtest Chart", stocks)

    df_chart = yf.Ticker(stock + ".NS").history(
        start=bt_date,
        end=bt_date + timedelta(days=1),
        interval="5m"
    )

    df_chart = df_chart.between_time("09:15", "15:30")

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
            marker=dict(
                size=12,
                color="green" if row["Type"] == "BIG BUY" else "red"
            ),
            text=[row["Type"]],
            textposition="top center"
        ))

    st.plotly_chart(fig, use_container_width=True)
