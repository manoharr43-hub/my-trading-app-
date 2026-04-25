import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V10", layout="wide")
st.title("🚀 NSE AI PRO V10 (ACCURACY BOOST)")
st_autorefresh(interval=60000, key="refresh")

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
# STOCK LIST
# =============================
stocks = ["HDFCBANK","ICICIBANK","SBIN","RELIANCE","INFY","TCS","ITC","LT","AXISBANK","KOTAKBANK"]

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
# BIG PLAYER V10 LOGIC
# =============================
def big_player(df, stock):
    if df.empty or len(df) < 30:
        return []

    df = df.copy()

    # ===== INDICATORS =====
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    df['VWAP'] = (df['Volume'] * (df['High']+df['Low']+df['Close'])/3).cumsum() / df['Volume'].cumsum()

    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    df['AvgVol'] = df['Volume'].rolling(20).mean()

    df['Body'] = abs(df['Close'] - df['Open'])
    df['Range'] = df['High'] - df['Low']
    df['StrongCandle'] = df['Body'] > (df['Range'] * 0.6)

    entries = []

    for i in range(25, len(df)):
        price = df['Close'].iloc[i]

        # ===== CONFIDENCE SCORE =====
        score = 0
        if price > df['EMA20'].iloc[i]: score += 1
        if price > df['EMA50'].iloc[i]: score += 1
        if price > df['VWAP'].iloc[i]: score += 1
        if df['RSI'].iloc[i] > 60: score += 1
        if df['Volume'].iloc[i] > df['AvgVol'].iloc[i]*3: score += 1

        confidence = f"{score}/5"

        # ===== BUY =====
        if (
            df['Volume'].iloc[i] > df['AvgVol'].iloc[i]*2.5 and
            price > df['EMA20'].iloc[i] > df['EMA50'].iloc[i] and
            price > df['VWAP'].iloc[i] and
            df['RSI'].iloc[i] > 55 and
            df['StrongCandle'].iloc[i]
        ):
            entries.append({
                "Stock": stock,
                "Type": "BIG BUY",
                "Price": price,
                "TimeRaw": df.index[i],
                "Time": clean_time(df.index[i]),
                "Confidence": confidence
            })

        # ===== SELL =====
        elif (
            df['Volume'].iloc[i] > df['AvgVol'].iloc[i]*2.5 and
            price < df['EMA20'].iloc[i] < df['EMA50'].iloc[i] and
            price < df['VWAP'].iloc[i] and
            df['RSI'].iloc[i] < 45 and
            df['StrongCandle'].iloc[i]
        ):
            entries.append({
                "Stock": stock,
                "Type": "BIG SELL",
                "Price": price,
                "TimeRaw": df.index[i],
                "Time": clean_time(df.index[i]),
                "Confidence": confidence
            })

    # Only latest signals
    if len(entries) > 0:
        entries = entries[-5:]

    return entries

# =============================
# STRENGTH
# =============================
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
        try:
            df = load_data(s)
            if df.empty: continue

            signals = big_player(df, s)
            all_big += signals

            strength_data.append({
                "Stock": s,
                "Strength %": strength_meter(df)
            })

        except Exception as e:
            st.warning(f"{s} error: {e}")

    all_big = sorted(all_big, key=lambda x: x["TimeRaw"])
    strength_df = pd.DataFrame(strength_data).sort_values(by="Strength %", ascending=False)

    st.session_state.live_big = all_big
    st.session_state.strength = strength_df

# =============================
# DISPLAY
# =============================
if len(st.session_state.live_big) > 0:

    st.subheader("🐋 BIG PLAYER SIGNALS")
    df_signals = pd.DataFrame(st.session_state.live_big)
    st.dataframe(df_signals.sort_values(by="TimeRaw", ascending=False))

    st.markdown("### ✅ BIG BUY")
    st.dataframe(df_signals[df_signals["Type"]=="BIG BUY"][["Stock","Price","Time","Confidence"]])

    st.markdown("### ❌ BIG SELL")
    st.dataframe(df_signals[df_signals["Type"]=="BIG SELL"][["Stock","Price","Time","Confidence"]])

    if not st.session_state.strength.empty:
        st.subheader("🔥 STRONG STOCKS")
        st.dataframe(st.session_state.strength.head(5))

        st.subheader("❄️ WEAK STOCKS")
        st.dataframe(st.session_state.strength.tail(5))

    # =============================
    # CHART
    # =============================
    stock = st.selectbox("📈 Chart", stocks)
    df_chart = load_data(stock)

    if df_chart.empty:
        st.warning("No data available")
    else:
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
            ).between_time("09:15","15:30")

            if df.empty: continue
            bt_big += big_player(df, s)

        except Exception as e:
            st.warning(f"{s} error: {e}")

    bt_big = sorted(bt_big, key=lambda x: x["TimeRaw"])
    bt_df = pd.DataFrame(bt_big)

    if not bt_df.empty:
        st.subheader("🐋 BACKTEST RESULTS")
        st.dataframe(bt_df[["Stock","Type","Price","Time","Confidence"]])

        stock = st.selectbox("📉 Backtest Chart", stocks)
        df_chart = yf.Ticker(stock + ".NS").history(
            start=bt_date,
            end=bt_date + timedelta(days=1),
            interval="5m"
        ).between_time("09:15","15:30")

        if df_chart.empty:
            st.warning("No data")
        else:
            fig = go.Figure(data=[go.Candlestick(
                x=df_chart.index,
                open=df_chart['Open'],
                high=df_chart['High'],
                low=df_chart['Low'],
                close=df_chart['Close']
            )])

            df_bt = bt_df[bt_df["Stock"] == stock]

            for _, row in df_bt.iterrows():
                fig.add_trace(go.Scatter(
                    x=[row["TimeRaw"]],
                    y=[row["Price"]],
                    mode="markers+text",
                    marker=dict(size=12, color="green" if row["Type"]=="BIG BUY" else "red"),
                    text=[f"{row['Type']} ({row['Confidence']})"],
                    textposition="top center"
                ))

            st.plotly_chart(fig, use_container_width=True)
