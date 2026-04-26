import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# =============================
# 1. CONFIG
# =============================
st.set_page_config(page_title="NSE AI PRO V22.2", layout="wide")
st.title("🚀 NSE AI PRO V22.2 - Smart Money + Backtest FIXED")

st_autorefresh(interval=60000, key="refresh")

# =============================
# 2. SECTORS
# =============================
sector_map = {
    "Banking": ["HDFCBANK", "ICICIBANK", "SBIN", "AXISBANK", "KOTAKBANK"],
    "IT": ["INFY", "TCS", "HCLTECH", "WIPRO", "TECHM"],
    "Auto": ["MARUTI", "M&M", "TATAMOTORS", "HEROMOTOCO"],
    "Oil & Metals": ["RELIANCE", "ONGC", "TATASTEEL", "HINDALCO"]
}

st.sidebar.header("⚙️ Settings")
sector = st.sidebar.selectbox("Sector", list(sector_map.keys()))
stocks = sector_map[sector]
timeframe = st.sidebar.selectbox("Interval", ["5m", "15m", "30m", "1h"])

sl_pct = st.sidebar.slider("Stop Loss (%)", 0.5, 5.0, 1.0) / 100
tgt_pct = st.sidebar.slider("Target (%)", 1.0, 10.0, 2.0) / 100

# =============================
# 3. DATA
# =============================
@st.cache_data(ttl=60)
def load_data(stock, interval, period="5d"):
    return yf.Ticker(stock + ".NS").history(period=period, interval=interval)

def indicators(df):
    df = df.copy()
    df["EMA20"] = df["Close"].ewm(span=20).mean()
    df["EMA50"] = df["Close"].ewm(span=50).mean()

    tp = (df["High"] + df["Low"] + df["Close"]) / 3
    df["VWAP"] = (tp * df["Volume"]).cumsum() / df["Volume"].cumsum()

    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    rs = gain.rolling(14).mean() / (loss.rolling(14).mean() + 1e-9)
    df["RSI"] = 100 - (100 / (1 + rs))

    df["AvgVol"] = df["Volume"].rolling(20).mean()
    return df

# =============================
# 4. SIGNAL ENGINE
# =============================
def get_signals(df, stock):
    df = indicators(df)
    signals = []

    for i in range(30, len(df)):
        row = df.iloc[i]
        prev = df.iloc[i - 1]

        price = round(row["Close"], 2)
        sig = None

        # Big player
        if row["Volume"] > row["AvgVol"] * 2.5:
            sig = "🔥 BIG BUY" if row["Close"] > row["Open"] else "💀 BIG SELL"

        # Bullish
        elif prev["Close"] < row["EMA20"] and row["Close"] > row["EMA20"] and row["RSI"] > 40:
            if row["EMA20"] > row["EMA50"]:
                sig = "🟢 BULLISH"

        # Bearish
        elif prev["Close"] > row["EMA20"] and row["Close"] < row["EMA20"] and row["RSI"] < 60:
            if row["EMA20"] < row["EMA50"]:
                sig = "🔴 BEARISH"

        if sig:
            if "BUY" in sig or "BULLISH" in sig:
                sl = round(price * (1 - sl_pct), 2)
                tgt = round(price * (1 + tgt_pct), 2)
            else:
                sl = round(price * (1 + sl_pct), 2)
                tgt = round(price * (1 - tgt_pct), 2)

            signals.append({
                "Stock": stock,
                "Type": sig,
                "Entry": price,
                "StopLoss": sl,
                "Target": tgt,
                "Time": df.index[i]
            })

    return signals

# =============================
# 5. LIVE SCAN
# =============================
if st.button("🚀 SCAN"):
    results = []

    for s in stocks:
        data = load_data(s, timeframe)
        if not data.empty:
            results.extend(get_signals(data, s))

    st.session_state.data = results

if "data" in st.session_state:
    df = pd.DataFrame(st.session_state.data)

    if not df.empty:
        df["Time"] = pd.to_datetime(df["Time"]).dt.strftime("%d-%m %I:%M %p")
        st.subheader("📊 Live Signals")
        st.dataframe(df.sort_values("Time", ascending=False), use_container_width=True)

# =============================
# 6. BACKTEST FIXED
# =============================
st.divider()
st.subheader("📊 Backtest Engine")

col1, col2 = st.columns([1, 3])

with col1:
    bt_stock = st.selectbox("Stock", stocks)
    bt_date = st.date_input("Date", datetime.now() - timedelta(days=1))

if st.button("🔍 RUN BACKTEST"):

    data = load_data(bt_stock, timeframe, period="2mo")

    if data.empty:
        st.error("No data")
        st.stop()

    data = data.copy()
    data.index = pd.to_datetime(data.index)

    data["date"] = data.index.date
    day_data = data[data["date"] == bt_date]

    if day_data.empty:
        st.warning("No data for selected date")
    else:
        signals = get_signals(data.drop(columns=["date"], errors="ignore"), bt_stock)

        day_signals = []
        for s in signals:
            try:
                if pd.to_datetime(s["Time"]).date() == bt_date:
                    day_signals.append(s)
            except:
                pass

        if day_signals:
            st.success(f"{len(day_signals)} signals found")

            df_bt = pd.DataFrame(day_signals)
            df_bt["Time"] = pd.to_datetime(df_bt["Time"]).dt.strftime("%H:%M")

            st.dataframe(df_bt[["Type", "Entry", "StopLoss", "Target", "Time"]])

        else:
            st.warning("No signals")

        # Chart always show
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=day_data.index,
            open=day_data["Open"],
            high=day_data["High"],
            low=day_data["Low"],
            close=day_data["Close"]
        ))

        fig.update_layout(
            title=f"{bt_stock} Backtest {bt_date}",
            template="plotly_dark",
            xaxis_rangeslider_visible=False
        )

        st.plotly_chart(fig, use_container_width=True)
