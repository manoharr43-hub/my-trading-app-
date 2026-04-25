import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import datetime as dt
import plotly.graph_objects as go

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V17", layout="wide")

st.title("🚀 NSE AI PRO V17 - CLEAN INSTITUTIONAL TERMINAL")

# =============================
# MARKET TIME FILTER
# =============================
now = dt.datetime.now().time()
market_open = dt.time(9, 15)
market_close = dt.time(15, 30)

market_live = market_open <= now <= market_close

# =============================
# SESSION BACKTEST
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
# SAFE DATA LOADER
# =============================
@st.cache_data(ttl=300)
def load_data(stock):
    try:
        df = yf.Ticker(stock + ".NS").history(period="5d", interval="5m")
        if df is None or df.empty or len(df) < 20:
            return None
        return df
    except:
        return None

# =============================
# CORE ENGINE
# =============================
def analyze(df):

    if df is None or len(df) < 20:
        return "NO DATA", "NO DATA", "NO DATA"

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

    # SMART MONEY
    if df['Volume'].iloc[-1] > vol_avg * 1.8:

        if breakout == "UP BREAKOUT":
            big_entry = "BIG BUY ENTRY"

        elif breakout == "DOWN BREAKOUT":
            big_entry = "BIG SELL ENTRY"

    return signal, breakout, big_entry

# =============================
# CHART SYSTEM
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

    # BREAKOUT MARKER
    if breakout != "NONE":
        fig.add_scatter(
            x=[df.index[-1]],
            y=[df['Close'].iloc[-1]],
            mode="markers+text",
            marker=dict(size=12, color="blue"),
            text=[breakout]
        )

    # BIG ENTRY MARKER
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
# MARKET STATUS
# =============================
st.subheader("⏱ MARKET STATUS")

if market_live:
    st.success("🟢 MARKET OPEN (9:15 - 3:30)")
else:
    st.error("🔴 MARKET CLOSED")

# =============================
# SECTOR SCANNER
# =============================
st.subheader("📡 NSE SECTOR SCANNER")

buy, sell, wait = [], [], []

for sector, stocks in sector_map.items():

    st.markdown(f"### 🔹 {sector}")

    table = []

    for s in stocks:

        df = load_data(s)

        if df is None:
            continue

        signal, breakout, big_entry = analyze(df)

        table.append({
            "Stock": s,
            "Signal": signal,
            "Breakout": breakout,
            "BigEntry": big_entry
        })

        if big_entry == "BIG BUY ENTRY":
            buy.append(s)
        elif big_entry == "BIG SELL ENTRY":
            sell.append(s)
        else:
            wait.append(s)

    st.dataframe(pd.DataFrame(table))

# =============================
# TODAY STOCK LIST
# =============================
st.subheader("🔥 TODAY STOCK LIST")

col1, col2, col3 = st.columns(3)

with col1:
    st.success("🚀 BUY")
    st.write(list(set(buy)))

with col2:
    st.error("💀 SELL")
    st.write(list(set(sell)))

with col3:
    st.info("⏳ WAIT")
    st.write(list(set(wait)))

# =============================
# STOCK CHART VIEW
# =============================
st.subheader("📊 STOCK CHART")

selected = st.selectbox("Select Stock", all_stocks)

df = load_data(selected)

show_chart(df, selected)

# =============================
# BACKTEST SYSTEM
# =============================
st.subheader("📁 BACKTEST SYSTEM")

bt_date = st.date_input("Select Backtest Date")

if st.button("RUN BACKTEST"):

    results = []

    for s in all_stocks:

        df = load_data(s)

        if df is None:
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

    st.success(f"✅ BACKTEST DONE ({bt_date})")
    st.dataframe(df_res)

# =============================
# BACKTEST HISTORY
# =============================
st.subheader("📁 BACKTEST HISTORY")

if len(st.session_state.bt_history) == 0:
    st.info("No backtest yet")
else:
    for i, df in enumerate(st.session_state.bt_history[::-1]):
        with st.expander(f"Run #{i+1}"):
            st.dataframe(df)
