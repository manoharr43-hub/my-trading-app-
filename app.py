import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V8", layout="wide")
st_autorefresh(interval=60000, key="refresh")

st.title("🚀 NSE AI PRO V8 - PAPER TRADING SYSTEM")
st.markdown("---")

# =============================
# SESSION STATE (PAPER TRADING)
# =============================
if "paper_trade" not in st.session_state:
    st.session_state.paper_trade = {
        "position": None,
        "entry_price": 0,
        "pnl": 0,
        "trades": []
    }

# =============================
# STOCKS
# =============================
stocks = ["TCS","INFY","HDFCBANK","SBIN","RELIANCE","ITC"]

# =============================
# DATA
# =============================
@st.cache_data(ttl=300)
def load_data(stock):
    return yf.Ticker(stock + ".NS").history(period="1d", interval="5m")

# =============================
# SIMPLE SIGNAL
# =============================
def signal_logic(df):

    ema20 = df['Close'].ewm(span=20).mean()
    ema50 = df['Close'].ewm(span=50).mean()

    if ema20.iloc[-1] > ema50.iloc[-1]:
        return "BUY"
    elif ema20.iloc[-1] < ema50.iloc[-1]:
        return "SELL"
    return "WAIT"

# =============================
# PAPER TRADING ENGINE (MAIN FIX)
# =============================
def paper_trade(stock, signal, price):

    acc = st.session_state.paper_trade

    # 🟢 BUY ENTRY
    if signal == "BUY" and acc["position"] is None:

        acc["position"] = "LONG"
        acc["entry_price"] = price

        acc["trades"].append({
            "Stock": stock,
            "Action": "BUY",
            "Price": price,
            "Time": datetime.now().strftime("%H:%M:%S")
        })

        st.success(f"🟢 PAPER BUY: {stock} @ {price}")

    # 🔴 SELL EXIT
    elif signal == "SELL" and acc["position"] == "LONG":

        entry = acc["entry_price"]
        pnl = price - entry

        acc["pnl"] += pnl
        acc["position"] = None

        acc["trades"].append({
            "Stock": stock,
            "Action": "SELL",
            "Price": price,
            "PnL": round(pnl,2),
            "Time": datetime.now().strftime("%H:%M:%S")
        })

        st.error(f"🔴 PAPER SELL: {stock} @ {price} | PnL: {round(pnl,2)}")

# =============================
# LIVE SCANNER + PAPER TRADE
# =============================
st.subheader("📡 LIVE SCANNER + PAPER TRADING")

for stock in stocks:

    df = load_data(stock)

    if df is None or len(df) < 50:
        continue

    signal = signal_logic(df)
    price = df['Close'].iloc[-1]

    st.write(f"**{stock} → {signal} → {price}**")

    # 👉 PAPER TRADE CALL
    paper_trade(stock, signal, price)

# =============================
# PAPER TRADING DASHBOARD
# =============================
st.markdown("---")

st.subheader("💰 PAPER TRADING DASHBOARD")

acc = st.session_state.paper_trade

st.metric("Total PnL", round(acc["pnl"],2))
st.write("📌 Position:", acc["position"])

st.dataframe(pd.DataFrame(acc["trades"]))

# =============================
# RESET BUTTON
# =============================
if st.button("🔄 RESET PAPER ACCOUNT"):

    st.session_state.paper_trade = {
        "position": None,
        "entry_price": 0,
        "pnl": 0,
        "trades": []
    }

    st.success("Account Reset Done")
