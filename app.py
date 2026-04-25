import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import datetime as dt
import plotly.graph_objects as go

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V18", layout="wide")

st.title("🚀 NSE AI PRO V18 - BREAKOUT TIME + CHART + BACKTEST TIME")

# =============================
# SESSION
# =============================
if "bt_history" not in st.session_state:
    st.session_state.bt_history = []

# =============================
# STOCKS
# =============================
stocks = ["RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","ITC"]

# =============================
# DATA
# =============================
@st.cache_data(ttl=300)
def load_data(stock):
    try:
        df = yf.Ticker(stock + ".NS").history(period="5d", interval="5m")
        if df is None or len(df) < 20:
            return None
        return df
    except:
        return None

# =============================
# ANALYSIS (WITH TIME)
# =============================
def analyze(df):

    if df is None or len(df) < 20:
        return "NO DATA", "NONE", "NONE", None

    df = df.dropna()

    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    price = df['Close'].iloc[-1]

    resistance = df['High'].rolling(20).max().iloc[-2]
    support = df['Low'].rolling(20).min().iloc[-2]

    vol_avg = df['Volume'].rolling(20).mean().iloc[-1]

    signal = "WAIT"
    breakout = "NONE"
    big_entry = "NONE"
    breakout_time = None

    # TREND
    if df['EMA20'].iloc[-1] > df['EMA50'].iloc[-1]:
        signal = "BUY"
    else:
        signal = "SELL"

    # BREAKOUT + TIME CAPTURE
    if price > resistance:
        breakout = "UP BREAKOUT"
        breakout_time = df.index[-1]

    elif price < support:
        breakout = "DOWN BREAKOUT"
        breakout_time = df.index[-1]

    # SMART MONEY
    if df['Volume'].iloc[-1] > vol_avg * 1.8:

        if breakout == "UP BREAKOUT":
            big_entry = "BIG BUY ENTRY"

        if breakout == "DOWN BREAKOUT":
            big_entry = "BIG SELL ENTRY"

    return signal, breakout, big_entry, breakout_time

# =============================
# CHART (TODAY FIX)
# =============================
def show_chart(df, stock):

    signal, breakout, big_entry, btime = analyze(df)

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

    # BREAKOUT MARKER
    if breakout != "NONE":
        st.info(f"📌 BREAKOUT: {breakout}")
        st.info(f"⏱ TIME: {btime}")

        fig.add_scatter(
            x=[df.index[-1]],
            y=[df['Close'].iloc[-1]],
            mode="markers+text",
            marker=dict(size=12, color="blue"),
            text=[breakout]
        )

    # BIG ENTRY
    if big_entry != "NONE":

        color = "green" if "BUY" in big_entry else "red"

        fig.add_scatter(
            x=[df.index[-1]],
            y=[df['Close'].iloc[-1]],
            mode="markers+text",
            marker=dict(size=14, color=color),
            text=[big_entry]
        )

    st.subheader(f"📊 {stock} | {signal}")
    st.plotly_chart(fig, use_container_width=True, key=stock)

# =============================
# TODAY CHART VIEW
# =============================
st.subheader("📊 TODAY CHART VIEW")

selected = st.selectbox("Select Stock", stocks)

df = load_data(selected)

if df is not None:
    show_chart(df, selected)
else:
    st.error("⚠️ NO DATA AVAILABLE")

# =============================
# SECTOR SCANNER
# =============================
st.subheader("📡 TODAY SCANNER")

buy, sell = [], []

for s in stocks:

    df = load_data(s)

    if df is None:
        continue

    signal, breakout, big_entry, btime = analyze(df)

    if big_entry == "BIG BUY ENTRY":
        buy.append(s)

    if big_entry == "BIG SELL ENTRY":
        sell.append(s)

col1, col2 = st.columns(2)

with col1:
    st.success("🚀 BUY STOCKS")
    st.write(buy)

with col2:
    st.error("💀 SELL STOCKS")
    st.write(sell)

# =============================
# BACKTEST WITH TIME
# =============================
st.subheader("📁 BACKTEST SYSTEM")

bt_date = st.date_input("Select Date")

if st.button("RUN BACKTEST"):

    run_time = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    results = []

    for s in stocks:

        df = load_data(s)

        if df is None:
            continue

        signal, breakout, big_entry, btime = analyze(df)

        results.append({
            "Stock": s,
            "Signal": signal,
            "Breakout": breakout,
            "BigEntry": big_entry,
            "BreakoutTime": str(btime)
        })

    df_res = pd.DataFrame(results)

    st.session_state.bt_history.append({
        "time": run_time,
        "date": str(bt_date),
        "data": df_res
    })

    st.success(f"✅ BACKTEST DONE @ {run_time}")
    st.dataframe(df_res)

# =============================
# BACKTEST HISTORY
# =============================
st.subheader("📁 BACKTEST HISTORY")

if len(st.session_state.bt_history) == 0:
    st.info("No backtest yet")
else:
    for i, item in enumerate(st.session_state.bt_history[::-1]):
        with st.expander(f"Run #{i+1} | {item['time']} | {item['date']}"):
            st.dataframe(item["data"])
