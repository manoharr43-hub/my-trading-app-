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
st.set_page_config(page_title="🔥 NSE AI PRO V21", layout="wide")
st.title("🚀 NSE AI PRO V21 - AI + Auto Trade + Smart Big Player")

st_autorefresh(interval=60000, key="refresh")

# =============================
# BACKTEST FOLDER
# =============================
BACKTEST_DIR = "backtests"
os.makedirs(BACKTEST_DIR, exist_ok=True)

# =============================
# SESSION
# =============================
if "signals" not in st.session_state:
    st.session_state.signals = []

# =============================
# SECTOR MAP
# =============================
sector_map = {
    "Banking": ["HDFCBANK","ICICIBANK","SBIN","AXISBANK","KOTAKBANK"],
    "IT": ["INFY","TCS","HCLTECH","WIPRO","TECHM"],
    "Auto": ["MARUTI","M&M","TATAMOTORS","HEROMOTOCO"],
    "FMCG": ["ITC","HINDUNILVR","NESTLEIND"],
    "Oil": ["RELIANCE","ONGC","BPCL"],
    "Metals": ["TATASTEEL","JSWSTEEL","HINDALCO"],
}

sector = st.sidebar.selectbox("📂 Sector", list(sector_map.keys()))
stocks = sector_map[sector]

# =============================
# DATA
# =============================
@st.cache_data(ttl=60)
def load_data(stock, interval="5m"):
    df = yf.Ticker(stock + ".NS").history(period="5d", interval=interval)
    return df

# =============================
# INDICATORS
# =============================
def indicators(df):
    df = df.copy()

    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    tp = (df['High'] + df['Low'] + df['Close']) / 3
    df['VWAP'] = (tp * df['Volume']).cumsum() / df['Volume'].cumsum()

    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    rs = gain.rolling(14).mean() / (loss.rolling(14).mean() + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))

    df['AvgVol'] = df['Volume'].rolling(20).mean()

    return df

# =============================
# AUTO TRADE ENGINE (SL/TP)
# =============================
def trade_engine(price, atr, side):
    if side == "BUY":
        return {
            "Entry": price,
            "SL": price - (1.5 * atr),
            "Target": price + (3 * atr)
        }
    else:
        return {
            "Entry": price,
            "SL": price + (1.5 * atr),
            "Target": price - (3 * atr)
        }

# =============================
# SMART BIG PLAYER DETECTION
# =============================
def big_player(df, stock):
    if df.empty or len(df) < 50:
        return []

    df = indicators(df)

    signals = []
    last = None

    for i in range(50, len(df)):
        price = df['Close'].iloc[i]

        vol_spike = df['Volume'].iloc[i] > df['AvgVol'].iloc[i] * 2
        trend_up = df['EMA20'].iloc[i] > df['EMA50'].iloc[i]

        buy = (
            price > df['VWAP'].iloc[i] and
            trend_up and
            df['RSI'].iloc[i] > 55 and
            vol_spike
        )

        sell = (
            price < df['VWAP'].iloc[i] and
            not trend_up and
            df['RSI'].iloc[i] < 45 and
            vol_spike
        )

        atr = (df['High'] - df['Low']).rolling(14).mean().iloc[i]

        if buy and last != "BUY":
            trade = trade_engine(price, atr, "BUY")
            signals.append({
                "Stock": stock,
                "Type": "AUTO BUY",
                "Price": price,
                "Time": df.index[i],
                **trade
            })
            last = "BUY"

        elif sell and last != "SELL":
            trade = trade_engine(price, atr, "SELL")
            signals.append({
                "Stock": stock,
                "Type": "AUTO SELL",
                "Price": price,
                "Time": df.index[i],
                **trade
            })
            last = "SELL"

    return signals[-10:]

# =============================
# LIVE SYSTEM
# =============================
if st.button("🚀 START AI LIVE TRADING"):
    all_signals = []

    for s in stocks:
        df = load_data(s, "5m")
        signals = big_player(df, s)
        all_signals.extend(signals)

    st.session_state.signals = all_signals

# =============================
# DISPLAY
# =============================
if st.session_state.signals:
    df_sig = pd.DataFrame(st.session_state.signals)

    st.subheader("🐋 AI AUTO SIGNALS (BIG PLAYER + SL/TP)")
    st.dataframe(df_sig)

    stock = st.selectbox("📊 Chart", stocks)
    df_chart = load_data(stock, "5m")

    if not df_chart.empty:
        fig = go.Figure(data=[go.Candlestick(
            x=df_chart.index,
            open=df_chart['Open'],
            high=df_chart['High'],
            low=df_chart['Low'],
            close=df_chart['Close']
        )])

        df_s = df_sig[df_sig["Stock"] == stock]

        for _, r in df_s.iterrows():
            fig.add_trace(go.Scatter(
                x=[r["Time"]],
                y=[r["Price"]],
                mode="markers",
                marker=dict(size=10, color="green" if "BUY" in r["Type"] else "red")
            ))

        st.plotly_chart(fig, use_container_width=True)

# =============================
# BACKTEST
# =============================
if st.checkbox("📊 BACKTEST MODE"):
    date = st.date_input("Select Date", datetime.now().date() - timedelta(days=1))

    bt_all = []

    for s in stocks:
        df = yf.Ticker(s + ".NS").history(period="5d", interval="5m")
        df = df[df.index.date == date]

        signals = big_player(df, s)
        bt_all.extend(signals)

    st.subheader("📊 BACKTEST RESULTS")

    if bt_all:
        st.dataframe(pd.DataFrame(bt_all))
    else:
        st.warning("No signals found")
