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
st.set_page_config(page_title="NSE AI PRO V23 FINAL", layout="wide")
st.title("🚀 NSE AI PRO V23 - CLEAN FIXED VERSION")

st_autorefresh(interval=180000, key="refresh")

# =============================
# SECTORS
# =============================
sector_map = {
    "Banking": ["HDFCBANK", "ICICIBANK", "SBIN", "AXISBANK", "KOTAKBANK"],
    "IT": ["INFY", "TCS", "HCLTECH", "WIPRO", "TECHM"],
    "Auto": ["MARUTI", "M&M", "TATAMOTORS", "HEROMOTOCO"],
    "Energy": ["RELIANCE", "ONGC", "IOC"],
    "Metals": ["TATASTEEL", "HINDALCO"],
    "FMCG": ["ITC", "HINDUNILVR"]
}

st.sidebar.header("⚙️ Settings")
sector = st.sidebar.selectbox("Sector", list(sector_map.keys()))
stocks = sector_map[sector]
timeframe = st.sidebar.selectbox("Timeframe", ["5m", "15m", "30m", "1h"])

sl_pct = st.sidebar.slider("SL %", 0.5, 5.0, 1.0) / 100
tgt_pct = st.sidebar.slider("Target %", 1.0, 10.0, 2.0) / 100

# =============================
# DATA LOADER (FIXED)
# =============================
@st.cache_data(ttl=120)
def load_data(stock):
    try:
        if timeframe == "5m":
            period = "7d"
        elif timeframe == "15m":
            period = "60d"
        else:
            period = "2mo"

        df = yf.download(stock + ".NS", period=period, interval=timeframe, progress=False)

        if df.empty:
            return df

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        return df

    except:
        return pd.DataFrame()

# =============================
# INDICATORS
# =============================
def indicators(df):
    df = df.copy()

    df["EMA20"] = df["Close"].ewm(span=20).mean()
    df["EMA50"] = df["Close"].ewm(span=50).mean()

    df["AvgVol"] = df["Volume"].rolling(20).mean()

    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    rs = gain.rolling(14).mean() / (loss.rolling(14).mean() + 1e-9)
    df["RSI"] = 100 - (100 / (1 + rs))

    return df

# =============================
# SMART ENGINE
# =============================
def smart_engine(df, stock):
    df = indicators(df)
    signals = []

    last_sig = None

    for i in range(30, len(df)):
        row = df.iloc[i]
        price = float(row["Close"])

        sig = None

        if row["Volume"] > row["AvgVol"] * 2:
            sig = "🔥 BIG BUY" if row["Close"] > row["Open"] else "💀 BIG SELL"

        elif row["EMA20"] > row["EMA50"] and row["RSI"] > 55:
            sig = "🟢 TREND BUY"

        elif row["EMA20"] < row["EMA50"] and row["RSI"] < 45:
            sig = "🔴 TREND SELL"

        if sig and sig != last_sig:
            last_sig = sig

            sl = price * (1 - sl_pct) if "BUY" in sig else price * (1 + sl_pct)
            tgt = price * (1 + tgt_pct) if "BUY" in sig else price * (1 - tgt_pct)

            signals.append({
                "Stock": stock,
                "Signal": sig,
                "Price": round(price, 2),
                "SL": round(sl, 2),
                "Target": round(tgt, 2),
                "Time": df.index[i]
            })

    return df, signals

# =============================
# LIVE SCAN
# =============================
if st.button("🚀 LIVE SCAN"):
    all_data = []

    for s in stocks:
        time.sleep(1)
        df = load_data(s)

        if not df.empty:
            _, sigs = smart_engine(df, s)

            for x in sigs[-2:]:
                all_data.append(x)

    st.session_state.live = all_data

# =============================
# LIVE DISPLAY
# =============================
if "live" in st.session_state:
    st.subheader("📡 LIVE SIGNALS")
    df_live = pd.DataFrame(st.session_state.live)
    df_live["Time"] = pd.to_datetime(df_live["Time"]).dt.strftime("%H:%M")
    st.dataframe(df_live, use_container_width=True)

# =============================
# BACKTEST (DATE FIXED)
# =============================
st.divider()
st.subheader("📊 BACKTEST (DATE FIXED)")

bt_stock = st.selectbox("Stock", stocks)
bt_date = st.date_input("Select Date", datetime.now() - timedelta(days=1))

if st.button("🔍 RUN BACKTEST"):

    df = load_data(bt_stock)

    if df.empty:
        st.error("No Data Available")
        st.stop()

    df.index = pd.to_datetime(df.index).tz_localize(None)

    selected_date = pd.to_datetime(bt_date).date()

    day_df = df[df.index.date == selected_date]

    if day_df.empty:
        st.error("No data for selected date (yfinance limit or holiday)")
        st.stop()

    _, signals = smart_engine(df, bt_stock)

    day_signals = [
        s for s in signals
        if pd.to_datetime(s["Time"]).date() == selected_date
    ]

    if len(day_signals) == 0:
        st.warning("No signals found for this date")
    else:
        st.success(f"{len(day_signals)} signals found")

        st.dataframe(pd.DataFrame(day_signals))

        fig = go.Figure(data=[
            go.Candlestick(
                x=day_df.index,
                open=day_df["Open"],
                high=day_df["High"],
                low=day_df["Low"],
                close=day_df["Close"]
            )
        ])

        fig.update_layout(
            title=f"{bt_stock} Backtest - {bt_date}",
            template="plotly_dark",
            xaxis_rangeslider_visible=False
        )

        st.plotly_chart(fig, use_container_width=True)
