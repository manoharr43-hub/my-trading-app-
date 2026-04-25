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
st.set_page_config(page_title="🔥 NSE AI PRO V11", layout="wide")
st.title("🚀 NSE AI PRO V11 (ZERO ERROR FINAL)")
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
# FUNCTIONS
# =============================
def clean_time(ts):
    return pd.to_datetime(ts).strftime("%I:%M %p").lstrip("0")

@st.cache_data(ttl=60)
def load_data(stock, period="1d"):
    df = yf.Ticker(stock + ".NS").history(period=period, interval="5m")
    if df.empty:
        return pd.DataFrame()
    return df.between_time("09:15","15:30")

# =============================
# BIG PLAYER LOGIC V11
# =============================
def big_player(df, stock):
    if df.empty or len(df) < 30:
        return []

    df = df.copy()

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
            entries.append({
                "Stock": stock,
                "Type": "BIG BUY",
                "Price": price,
                "TimeRaw": df.index[i],
                "Time": clean_time(df.index[i]),
                "Confidence": confidence
            })

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
        try:
            df = load_data(s)
            if df.empty:
                continue

            all_big += big_player(df, s)
            strength_data.append({"Stock": s, "Strength %": strength_meter(df)})

        except Exception as e:
            st.warning(f"{s} error: {e}")

    st.session_state.live_big = sorted(all_big, key=lambda x: x["TimeRaw"])
    st.session_state.strength = pd.DataFrame(strength_data).sort_values(by="Strength %", ascending=False)

# =============================
# DISPLAY LIVE
# =============================
if st.session_state.live_big:

    df_signals = pd.DataFrame(st.session_state.live_big)

    st.subheader("🐋 BIG PLAYER SIGNALS")
    st.dataframe(df_signals.sort_values(by="TimeRaw", ascending=False), use_container_width=True)

    st.markdown("### ✅ BIG BUY")
    st.dataframe(df_signals[df_signals["Type"]=="BIG BUY"][["Stock","Price","Time","Confidence"]], use_container_width=True)

    st.markdown("### ❌ BIG SELL")
    st.dataframe(df_signals[df_signals["Type"]=="BIG SELL"][["Stock","Price","Time","Confidence"]], use_container_width=True)

    if not st.session_state.strength.empty:
        st.subheader("🔥 STRONG STOCKS")
        st.dataframe(st.session_state.strength.head(5), use_container_width=True)

        st.subheader("❄️ WEAK STOCKS")
        st.dataframe(st.session_state.strength.tail(5), use_container_width=True)

    # ===== CHART =====
    stock = st.selectbox("📈 Chart", stocks, key="live_stock")
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

        st.plotly_chart(fig, use_container_width=True, key=f"live_chart_{stock}_{datetime.now().timestamp()}")
    else:
        st.warning("No data for chart")

# =============================
# BACKTEST
# =============================
if st.checkbox("📊 Enable Backtest"):

    bt_date = st.date_input("Select Date", datetime.now().date() - timedelta(days=1), key="bt_date")

    bt_big = []
    for s in stocks:
        try:
            df = yf.Ticker(s + ".NS").history(
                start=bt_date,
                end=bt_date + timedelta(days=1),
                interval="5m"
            ).between_time("09:15","15:30")

            if df.empty:
                continue

            bt_big += big_player(df, s)

        except Exception as e:
            st.warning(f"{s} error: {e}")

    bt_df = pd.DataFrame(sorted(bt_big, key=lambda x: x["TimeRaw"]))
    st.session_state.bt_df = bt_df

    if not bt_df.empty:

        st.subheader("🐋 BACKTEST RESULTS")
        st.dataframe(bt_df[["Stock","Type","Price","Time","Confidence"]], use_container_width=True)

        stock = st.selectbox("📉 Backtest Chart", stocks, key="bt_stock")

        df_chart = yf.Ticker(stock + ".NS").history(
            start=bt_date,
            end=bt_date + timedelta(days=1),
            interval="5m"
        ).between_time("09:15","15:30")

        if not df_chart.empty:
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

            st.plotly_chart(fig, use_container_width=True, key=f"bt_chart_{stock}_{datetime.now().timestamp()}")
        else:
            st.warning("No backtest data")
