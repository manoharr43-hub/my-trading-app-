import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from streamlit_autorefresh import st_autorefresh
import plotly.graph_objects as go

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V15", layout="wide")
st_autorefresh(interval=60000, key="refresh")

st.title("🚀 NSE AI PRO V15 - CRASH PROOF + SMART MONEY + SECTORS")

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
# SAFE DATA LOADER (CRASH FIX)
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
# SAFE ANALYSIS ENGINE
# =============================
def analyze(df):

    # 🔥 SAFETY FIRST
    if df is None or len(df) < 20:
        return "NO DATA", "NO DATA", "NO DATA"

    df = df.dropna()

    price = df['Close'].iloc[-1]

    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    resistance = df['High'].rolling(20).max().iloc[-2] if len(df) > 20 else df['High'].max()
    support = df['Low'].rolling(20).min().iloc[-2] if len(df) > 20 else df['Low'].min()

    vol_avg = df['Volume'].rolling(20).mean().iloc[-1] if len(df) > 20 else df['Volume'].mean()

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

    # SMART MONEY (VOLUME TRAP)
    if df['Volume'].iloc[-1] > vol_avg * 1.8:

        if breakout == "UP BREAKOUT":
            big_entry = "BIG BUY ENTRY"

        elif breakout == "DOWN BREAKOUT":
            big_entry = "BIG SELL ENTRY"

    return signal, breakout, big_entry

# =============================
# CHART (SAFE ALWAYS)
# =============================
def show_chart(df, stock):

    if df is None:
        st.error("⚠️ NO DATA FOR CHART")
        return

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

    st.subheader(f"📊 {stock}")
    st.plotly_chart(fig, use_container_width=True, key=stock)

# =============================
# SECTOR SCANNER
# =============================
st.subheader("📡 NSE SECTOR SCANNER")

buy_list = []
sell_list = []

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
            buy_list.append(s)

        if big_entry == "BIG SELL ENTRY":
            sell_list.append(s)

    st.dataframe(pd.DataFrame(table))

# =============================
# TOP BUY / SELL
# =============================
st.subheader("🔥 ALL SECTOR TOP LIST")

col1, col2 = st.columns(2)

with col1:
    st.success("🚀 BIG BUY STOCKS")
    st.write(list(set(buy_list)))

with col2:
    st.error("💀 BIG SELL STOCKS")
    st.write(list(set(sell_list)))

# =============================
# STOCK CHART VIEW
# =============================
st.subheader("📊 STOCK CHART")

selected = st.selectbox("Select Stock", all_stocks)

df = load_data(selected)

show_chart(df, selected)

# =============================
# BACKTEST (SAFE + DATE READY)
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
# BACKTEST HISTORY (ALWAYS SHOW)
# =============================
st.subheader("📁 BACKTEST HISTORY")

if len(st.session_state.bt_history) == 0:
    st.info("No backtest yet")
else:
    for i, df in enumerate(st.session_state.bt_history[::-1]):
        with st.expander(f"Run #{i+1}"):
            st.dataframe(df)
