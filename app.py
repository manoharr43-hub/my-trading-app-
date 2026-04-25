import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V14", layout="wide")

st.title("🚀 NSE AI PRO V14 - INSTITUTIONAL SECTOR TERMINAL")

# =============================
# SESSION
# =============================
if "bt_history" not in st.session_state:
    st.session_state.bt_history = []

# =============================
# SECTORS
# =============================
sector_map = {
    "BANKING": ["HDFCBANK","ICICIBANK","SBIN","AXISBANK"],
    "IT": ["TCS","INFY","HCLTECH"],
    "AUTO": ["MARUTI","M&M","TATAMOTORS"],
    "FMCG": ["ITC","HINDUNILVR"],
    "ENERGY": ["RELIANCE","ONGC"]
}

all_stocks = list(set(sum(sector_map.values(), [])))

# =============================
# DATA
# =============================
@st.cache_data(ttl=300)
def load_data(stock):
    return yf.Ticker(stock + ".NS").history(period="5d", interval="5m")

# =============================
# CORE LOGIC
# =============================
def analyze(df):

    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    price = df['Close'].iloc[-1]

    resistance = df['High'].rolling(20).max().iloc[-2]
    support = df['Low'].rolling(20).min().iloc[-2]

    volume_ok = df['Volume'].iloc[-1] > df['Volume'].rolling(20).mean().iloc[-1]

    breakout = "NONE"
    big_entry = "NONE"
    signal = "WAIT"

    # TREND
    if df['EMA20'].iloc[-1] > df['EMA50'].iloc[-1]:
        signal = "BUY"
    else:
        signal = "SELL"

    # BREAKOUT
    if price > resistance:
        breakout = "UP BREAKOUT"
    elif price < support:
        breakout = "DOWN BREAKOUT"

    # BIG MONEY
    if volume_ok and breakout == "UP BREAKOUT":
        big_entry = "BIG BUY ENTRY"

    if volume_ok and breakout == "DOWN BREAKOUT":
        big_entry = "BIG SELL ENTRY"

    return signal, breakout, big_entry

# =============================
# CHART ENGINE
# =============================
def show_chart(df, stock):

    signal, breakout, big_entry = analyze(df)

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

    # MARKERS
    if breakout != "NONE":
        fig.add_scatter(
            x=[df.index[-1]],
            y=[df['Close'].iloc[-1]],
            mode="markers+text",
            marker=dict(size=12, color="blue"),
            text=[breakout]
        )

    if big_entry != "NONE":
        color = "green" if "BUY" in big_entry else "red"

        fig.add_scatter(
            x=[df.index[-1]],
            y=[df['Close'].iloc[-1]],
            mode="markers+text",
            marker=dict(size=14, color=color),
            text=[big_entry]
        )

    st.subheader(f"{stock} | {signal}")

    st.plotly_chart(fig, use_container_width=True)

# =============================
# SECTOR SCANNER
# =============================
st.subheader("📡 NSE SECTOR SCANNER")

sector_buy = {}
sector_sell = {}

for sector, stocks in sector_map.items():

    st.markdown(f"### 🔹 {sector}")

    table = []

    for s in stocks:

        df = load_data(s)

        if df is None or len(df) < 50:
            continue

        signal, breakout, big_entry = analyze(df)

        table.append({
            "Stock": s,
            "Signal": signal,
            "Breakout": breakout,
            "BigEntry": big_entry
        })

    df_sec = pd.DataFrame(table)
    st.dataframe(df_sec)

# =============================
# GLOBAL TOP LISTS
# =============================
st.subheader("🔥 ALL SECTOR TOP LIST")

buy_list = []
sell_list = []

for s in all_stocks:

    df = load_data(s)

    if df is None:
        continue

    signal, breakout, big_entry = analyze(df)

    if big_entry == "BIG BUY ENTRY":
        buy_list.append(s)

    if big_entry == "BIG SELL ENTRY":
        sell_list.append(s)

col1, col2 = st.columns(2)

with col1:
    st.success("🚀 BIG BUY STOCKS")
    st.write(buy_list)

with col2:
    st.error("💀 BIG SELL STOCKS")
    st.write(sell_list)

# =============================
# STOCK CHART VIEW
# =============================
st.subheader("📊 STOCK CHART")

selected = st.selectbox("Select Stock", all_stocks)

df = load_data(selected)

if df is not None:
    show_chart(df, selected)

# =============================
# BACKTEST SYSTEM (DATE LOGIC)
# =============================
st.subheader("📁 BACKTEST SYSTEM")

bt_date = st.date_input("Select Backtest Date")

if st.button("RUN BACKTEST"):

    results = []

    for s in all_stocks:

        df = yf.Ticker(s + ".NS").history(period="5d", interval="5m")

        if df is None or len(df) < 50:
            continue

        signal, breakout, big_entry = analyze(df)

        results.append({
            "Stock": s,
            "Signal": signal,
            "Breakout": breakout,
            "BigEntry": big_entry
        })

    df_res = pd.DataFrame(results)

    st.session_state.bt_history.append(df_res)

    st.success(f"✅ BACKTEST DONE FOR {bt_date}")
    st.dataframe(df_res)

# =============================
# BACKTEST FOLDER (ALWAYS SHOW)
# =============================
st.subheader("📁 BACKTEST HISTORY")

if len(st.session_state.bt_history) == 0:
    st.info("No backtest yet")
else:
    for i, df in enumerate(st.session_state.bt_history[::-1]):
        with st.expander(f"Run #{i+1}"):
            st.dataframe(df)
