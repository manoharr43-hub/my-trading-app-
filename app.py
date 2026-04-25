import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from streamlit_autorefresh import st_autorefresh
import plotly.graph_objects as go

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V13", layout="wide")
st_autorefresh(interval=60000, key="refresh")

st.title("🚀 NSE AI PRO V13 - CLEAN + STABLE + SMART MONEY")

# =============================
# SESSION SAFE
# =============================
if "bt_history" not in st.session_state:
    st.session_state.bt_history = []

# =============================
# STOCK LIST
# =============================
stocks = ["RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","ITC","LT"]

# =============================
# SAFE DATA LOADER
# =============================
@st.cache_data(ttl=300)
def load_data(stock, tf="5m"):
    try:
        df = yf.Ticker(stock + ".NS").history(period="5d", interval=tf)
        if df is None or len(df) < 10:
            return None
        return df
    except:
        return None

# =============================
# SMART MONEY LOGIC
# =============================
def smart_money(df):

    if df is None or len(df) < 20:
        return "NO DATA"

    price = df['Close'].iloc[-1]

    resistance = df['High'].rolling(20).max().iloc[-2] if len(df) > 20 else df['High'].max()
    support = df['Low'].rolling(20).min().iloc[-2] if len(df) > 20 else df['Low'].min()

    vol_avg = df['Volume'].rolling(20).mean().iloc[-1] if len(df) > 20 else df['Volume'].mean()

    vol_spike = df['Volume'].iloc[-1] > vol_avg * 1.8

    if vol_spike and price > resistance:
        return "🔥 DISTRIBUTION / BUY TRAP"

    if vol_spike and price < support:
        return "🔥 ACCUMULATION / SELL TRAP"

    if vol_spike:
        return "🧠 SMART MONEY ACTIVE"

    return "NORMAL"

# =============================
# TREND
# =============================
def trend(df):
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    return "UPTREND" if df['EMA20'].iloc[-1] > df['EMA50'].iloc[-1] else "DOWNTREND"

# =============================
# SIGNAL ENGINE
# =============================
def signals(df):

    price = df['Close'].iloc[-1]

    resistance = df['High'].rolling(20).max().iloc[-2] if len(df) > 20 else df['High'].max()
    support = df['Low'].rolling(20).min().iloc[-2] if len(df) > 20 else df['Low'].min()

    breakout = "NONE"
    big_entry = "NONE"

    vol_avg = df['Volume'].rolling(20).mean().iloc[-1] if len(df) > 20 else df['Volume'].mean()

    if price > resistance:
        breakout = "UP BREAKOUT"
    elif price < support:
        breakout = "DOWN BREAKOUT"

    if df['Volume'].iloc[-1] > vol_avg * 1.8:

        if breakout == "UP BREAKOUT":
            big_entry = "BIG BUY ENTRY"

        if breakout == "DOWN BREAKOUT":
            big_entry = "BIG SELL ENTRY"

    return breakout, big_entry

# =============================
# CHART (SAFE + ALWAYS SHOW)
# =============================
def show_chart(df, stock):

    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close']
    ))

    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['Close'].ewm(span=20).mean(),
        name="EMA20"
    ))

    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['Close'].ewm(span=50).mean(),
        name="EMA50"
    ))

    breakout, big_entry = signals(df)
    sm = smart_money(df)

    # INFO PANEL
    st.info(f"🧠 SMART MONEY: {sm}")
    st.success(f"📌 BREAKOUT: {breakout}")
    st.warning(f"💰 BIG ENTRY: {big_entry}")

    fig.update_layout(title=f"{stock}", height=550)

    st.plotly_chart(fig, use_container_width=True, key=stock)

# =============================
# LIVE VIEW
# =============================
st.subheader("📊 LIVE CHART")

selected = st.selectbox("Select Stock", stocks)

df = load_data(selected)

if df is None:
    st.error("⚠️ DATA NOT AVAILABLE")
else:
    show_chart(df, selected)

# =============================
# SCANNER
# =============================
st.subheader("🔥 MARKET SCANNER")

buy, sell = [], []

for s in stocks:

    df = load_data(s)

    if df is None:
        continue

    sm = smart_money(df)
    tr = trend(df)

    if "BUY TRAP" in sm and tr == "UPTREND":
        sell.append(s)

    if "SELL TRAP" in sm and tr == "DOWNTREND":
        buy.append(s)

col1, col2 = st.columns(2)

with col1:
    st.success("🚀 STRONG BUY")
    st.write(buy)

with col2:
    st.error("💀 STRONG SELL")
    st.write(sell)

# =============================
# BACKTEST (FIXED + ALWAYS SHOW)
# =============================
st.subheader("📁 BACKTEST FOLDER")

if st.button("RUN BACKTEST"):

    results = []

    for s in stocks:

        df = load_data(s)

        if df is None:
            continue

        sm = smart_money(df)
        tr = trend(df)
        br, be = signals(df)

        results.append({
            "Stock": s,
            "Trend": tr,
            "SmartMoney": sm,
            "Breakout": br,
            "BigEntry": be
        })

    df_res = pd.DataFrame(results)

    st.session_state.bt_history.append(df_res)

    st.success("✅ BACKTEST DONE")
    st.dataframe(df_res)

# ALWAYS SHOW HISTORY
if len(st.session_state.bt_history) == 0:
    st.info("No backtest yet")
else:
    for i, df in enumerate(st.session_state.bt_history[::-1]):
        with st.expander(f"Run #{i+1}"):
            st.dataframe(df)
