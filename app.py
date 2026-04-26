import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
import os

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V27 FIX", layout="wide")
st.title("🚀 NSE AI PRO V27 - ZERO ERROR BACKTEST")

st_autorefresh(interval=180000, key="refresh")

# =============================
# SECTORS
# =============================
sector_map = {
    "Banking": ["HDFCBANK","ICICIBANK","SBIN","AXISBANK","KOTAKBANK"],
    "IT": ["INFY","TCS","HCLTECH","WIPRO","TECHM"],
    "Auto": ["MARUTI","M&M","TATAMOTORS","HEROMOTOCO"],
    "Energy": ["RELIANCE","ONGC","IOC"],
    "Metals": ["TATASTEEL","HINDALCO"],
    "FMCG": ["ITC","HINDUNILVR"]
}

st.sidebar.header("⚙️ SETTINGS")
sector = st.sidebar.selectbox("Sector", list(sector_map.keys()))
stocks = sector_map[sector]

timeframe = st.sidebar.selectbox("Timeframe", ["5m","15m","30m","1h"])

sl_pct = st.sidebar.slider("SL %",0.5,5.0,1.0)/100
tgt_pct = st.sidebar.slider("Target %",1.0,10.0,2.0)/100

# =============================
# DATA LOADER
# =============================
@st.cache_data(ttl=120)
def load_data(stock):
    try:
        period = "7d" if timeframe=="5m" else "60d" if timeframe=="15m" else "2mo"
        df = yf.download(stock+".NS", period=period, interval=timeframe, progress=False)

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
    df["VOL_AVG"] = df["Volume"].rolling(20).mean()

    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    rs = gain.rolling(14).mean() / (loss.rolling(14).mean()+1e-9)
    df["RSI"] = 100 - (100/(1+rs))

    return df

# =============================
# SIGNAL ENGINE
# =============================
def generate_signals(df, stock):
    df = indicators(df)

    signals = []
    last = None

    for i in range(30, len(df)):
        row = df.iloc[i]
        price = row["Close"]

        sig = None

        if row["Volume"] > row["VOL_AVG"] * 2:
            sig = "🔥 BIG BUY" if row["Close"] > row["Open"] else "💀 BIG SELL"

        elif row["EMA20"] > row["EMA50"] and row["RSI"] > 55:
            sig = "🟢 TREND BUY"

        elif row["EMA20"] < row["EMA50"] and row["RSI"] < 45:
            sig = "🔴 TREND SELL"

        if sig and sig != last:
            last = sig

            sl = price * (1-sl_pct) if "BUY" in sig else price * (1+sl_pct)
            tgt = price * (1+tgt_pct) if "BUY" in sig else price * (1-tgt_pct)

            signals.append({
                "Stock": stock,
                "Signal": sig,
                "Price": round(price,2),
                "SL": round(sl,2),
                "Target": round(tgt,2),
                "Time": df.index[i]
            })

    return signals

# =============================
# LIVE SCAN
# =============================
if st.button("🚀 LIVE SCAN"):
    all_signals = []

    for s in stocks:
        time.sleep(0.5)
        df = load_data(s)

        if not df.empty:
            all_signals.extend(generate_signals(df, s))

    st.session_state.live = all_signals

# =============================
# LIVE DISPLAY
# =============================
if "live" in st.session_state:
    st.subheader("📡 LIVE SIGNALS")

    live_df = pd.DataFrame(st.session_state.live)

    if not live_df.empty:
        live_df["Time"] = pd.to_datetime(live_df["Time"]).dt.strftime("%I:%M %p")
        st.dataframe(live_df, use_container_width=True)
    else:
        st.warning("No signals")

# =============================
# BACKTEST FIX (FINAL SAFE)
# =============================
st.divider()
st.subheader("📊 BACKTEST - ZERO ERROR FIX")

bt_stock = st.selectbox("Stock", stocks)
bt_date = st.date_input("Select Date", datetime.now()-timedelta(days=1))

BACKTEST_DIR = "backtests"
os.makedirs(BACKTEST_DIR, exist_ok=True)

if st.button("🔍 RUN BACKTEST"):

    df = load_data(bt_stock)

    if df.empty:
        st.error("No Data Found")
        st.stop()

    # =============================
    # 🔥 TIMEZONE + TYPE FIX (MAIN FIX)
    # =============================
    df.index = pd.to_datetime(df.index)

    if hasattr(df.index, "tz") and df.index.tz is not None:
        df.index = df.index.tz_convert(None)

    # =============================
    # DATE FILTER SAFE
    # =============================
    start = pd.Timestamp(bt_date)
    end = start + pd.Timedelta(days=1)

    day_df = df.loc[(df.index >= start) & (df.index < end)]

    if day_df.empty:
        st.error("⚠️ No data for selected date (market closed / not available)")
        st.stop()

    signals = generate_signals(day_df, bt_stock)

    if len(signals) == 0:
        st.warning("No signals found")
        result_df = pd.DataFrame()
    else:
        st.success(f"{len(signals)} signals found")

        result_df = pd.DataFrame(signals)
        result_df["Time"] = pd.to_datetime(result_df["Time"]).dt.strftime("%I:%M %p")

        st.dataframe(result_df, use_container_width=True)

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

    # SAVE
    file_path = f"{BACKTEST_DIR}/{bt_stock}_{bt_date}.csv"
    result_df.to_csv(file_path, index=False)

    st.download_button(
        "⬇️ Download CSV",
        data=result_df.to_csv(index=False).encode(),
        file_name=f"{bt_stock}_{bt_date}.csv",
        mime="text/csv"
    )

    # FILE LIST
    st.sidebar.subheader("📂 BACKTEST FILES")
    files = os.listdir(BACKTEST_DIR)

    if files:
        for f in files:
            st.sidebar.write(f)
    else:
        st.sidebar.write("No files yet")
