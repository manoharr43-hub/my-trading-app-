import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="NSE AI PRO V22.5", layout="wide")
st.title("🚀 NSE AI PRO V22.5 - FINAL FIXED VERSION")

st_autorefresh(interval=180000, key="refresh")

# =============================
# SECTORS
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
# SMART DATA LOADER (FIXED)
# =============================
@st.cache_data(ttl=300)
def load_data(stock, interval):
    try:
        time.sleep(0.7)

        # 🔥 SMART PERIOD FIX (IMPORTANT)
        if interval == "5m":
            period = "7d"
        elif interval == "15m":
            period = "60d"
        else:
            period = "2mo"

        df = yf.download(
            stock + ".NS",
            period=period,
            interval=interval,
            progress=False,
            threads=False
        )

        if df is None or df.empty:
            return pd.DataFrame()

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        return df

    except:
        return pd.DataFrame()

# =============================
# INDICATORS
# =============================
def apply_indicators(df):
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
# SIGNAL ENGINE (CLEAN)
# =============================
def get_signals(df, stock):
    df = apply_indicators(df)
    signals = []

    last_signal = {}

    for i in range(30, len(df)):
        row = df.iloc[i]
        price = float(row["Close"])

        sig = None

        if row["Volume"] > row["AvgVol"] * 2.5:
            sig = "🔥 BIG BUY" if row["Close"] > row["Open"] else "💀 BIG SELL"

        elif row["EMA20"] > row["EMA50"] and row["RSI"] > 40:
            sig = "🟢 Bullish"

        elif row["EMA20"] < row["EMA50"] and row["RSI"] < 60:
            sig = "🔴 Bearish"

        # 🔥 FIX: duplicate control
        if sig:
            if last_signal.get(stock) == sig:
                continue
            last_signal[stock] = sig

            if "BUY" in sig or "Bullish" in sig:
                sl = price * (1 - sl_pct)
                tgt = price * (1 + tgt_pct)
            else:
                sl = price * (1 + sl_pct)
                tgt = price * (1 - tgt_pct)

            signals.append({
                "Stock": stock,
                "Type": sig,
                "Entry": round(price, 2),
                "StopLoss": round(sl, 2),
                "Target": round(tgt, 2),
                "Time": df.index[i]
            })

    return signals

# =============================
# LIVE SCAN (FIXED OLD DATA ISSUE)
# =============================
if st.button("🚀 SCAN FOR TRADES"):
    results = []

    for s in stocks:
        time.sleep(1)
        df = load_data(s, timeframe)

        if not df.empty:
            results += get_signals(df, s)

    # 🔥 FIX: clear old cache issue
    st.session_state.data = results

# =============================
# DISPLAY
# =============================
if "data" in st.session_state and st.session_state.data:
    df_res = pd.DataFrame(st.session_state.data)
    df_res["Time"] = pd.to_datetime(df_res["Time"]).dt.strftime("%d-%m %I:%M %p")

    st.subheader("🎯 Live Signals")
    st.dataframe(df_res.sort_values("Time", ascending=False), use_container_width=True)

# =============================
# BACKTEST (FULL FIXED)
# =============================
st.divider()
st.subheader("📊 Backtest Engine")

col1, col2 = st.columns([1, 3])

with col1:
    bt_stock = st.selectbox("Stock", stocks, key="bt_stock")
    bt_date = st.date_input("Date", datetime.now() - timedelta(days=1), key="bt_date")

if st.button("🔍 RUN BACKTEST"):

    time.sleep(1)

    data = load_data(bt_stock, timeframe)

    if data.empty:
        st.error("No data available")
        st.stop()

    data.index = pd.to_datetime(data.index).tz_localize(None)

    # 🔥 FIX: safe date match
    bt_date = pd.to_datetime(bt_date).date()
    day_data = data[data.index.date == bt_date]

    if day_data.empty:
        st.error("No data for selected date (yfinance limit or holiday)")
        st.stop()

    signals = get_signals(data, bt_stock)

    day_signals = [
        s for s in signals
        if pd.to_datetime(s["Time"]).date() == bt_date
    ]

    if day_signals:
        st.success(f"{len(day_signals)} signals found")

        df_bt = pd.DataFrame(day_signals)
        df_bt["Time"] = pd.to_datetime(df_bt["Time"]).dt.strftime("%I:%M %p")

        st.dataframe(df_bt, use_container_width=True)

        fig = go.Figure(data=[
            go.Candlestick(
                x=day_data.index,
                open=day_data["Open"],
                high=day_data["High"],
                low=day_data["Low"],
                close=day_data["Close"]
            )
        ])

        fig.update_layout(
            title=f"{bt_stock} Backtest",
            template="plotly_dark",
            xaxis_rangeslider_visible=False
        )

        st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning("No signals found for this date")
