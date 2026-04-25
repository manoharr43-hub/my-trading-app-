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
st.set_page_config(page_title="🤖 NSE AUTO TRADER V10", layout="wide")
st.title("🤖 NSE AUTO TRADER V10 (AUTO PAPER TRADING)")
st_autorefresh(interval=60000, key="refresh")

# =============================
# SESSION INIT
# =============================
if "trades" not in st.session_state:
    st.session_state.trades = []
if "balance" not in st.session_state:
    st.session_state.balance = 100000  # demo capital

# =============================
# STOCKS
# =============================
stocks = ["HDFCBANK","ICICIBANK","RELIANCE","INFY","TCS","SBIN"]

# =============================
# LOAD DATA
# =============================
@st.cache_data(ttl=60)
def load(stock):
    df = yf.Ticker(stock + ".NS").history(period="1d", interval="5m")
    return df.between_time("09:15","15:30")

# =============================
# SIGNAL LOGIC (UPGRADED)
# =============================
def signal(df):
    if len(df) < 30:
        return None

    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    df['AvgVol'] = df['Volume'].rolling(20).mean()

    last = df.iloc[-1]

    if last['Volume'] > last['AvgVol']*2.5 and last['Close'] > last['EMA20'] > last['EMA50']:
        return "BUY"
    elif last['Volume'] > last['AvgVol']*2.5 and last['Close'] < last['EMA20'] < last['EMA50']:
        return "SELL"
    return None

# =============================
# AUTO TRADING ENGINE
# =============================
if st.button("🚀 START AUTO TRADING"):
    for s in stocks:
        df = load(s)
        sig = signal(df)

        if sig:
            price = df['Close'].iloc[-1]
            qty = int(10000 / price)

            trade = {
                "Stock": s,
                "Type": sig,
                "Entry": price,
                "Time": datetime.now().strftime("%H:%M"),
                "Qty": qty,
                "Exit": None,
                "PnL": 0
            }

            st.session_state.trades.append(trade)

# =============================
# AUTO EXIT LOGIC
# =============================
for t in st.session_state.trades:
    if t["Exit"] is None:
        df = load(t["Stock"])
        price = df['Close'].iloc[-1]

        # 1% target / 0.5% SL
        if t["Type"] == "BUY":
            if price >= t["Entry"] * 1.01 or price <= t["Entry"] * 0.995:
                t["Exit"] = price
        else:
            if price <= t["Entry"] * 0.99 or price >= t["Entry"] * 1.005:
                t["Exit"] = price

        if t["Exit"]:
            pnl = (t["Exit"] - t["Entry"]) * t["Qty"]
            if t["Type"] == "SELL":
                pnl = -pnl

            t["PnL"] = round(pnl, 2)
            st.session_state.balance += pnl

# =============================
# DISPLAY
# =============================
st.subheader("💼 Trades")
df_trades = pd.DataFrame(st.session_state.trades)
st.dataframe(df_trades)

st.subheader("💰 Balance")
st.success(f"₹ {round(st.session_state.balance,2)}")

# =============================
# CHART
# =============================
stock = st.selectbox("Chart", stocks)
df = load(stock)

fig = go.Figure(data=[go.Candlestick(
    x=df.index,
    open=df['Open'],
    high=df['High'],
    low=df['Low'],
    close=df['Close']
)])

st.plotly_chart(fig, use_container_width=True)
