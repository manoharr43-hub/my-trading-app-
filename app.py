import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time as dtime
import plotly.graph_objects as go

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V36", layout="wide")
st.title("🚀 NSE AI PRO V36 - FINAL STABLE BUILD")

# =============================
# SETTINGS
# =============================
sector_map = {
    "Banking": ["HDFCBANK","ICICIBANK","SBIN","AXISBANK","KOTAKBANK"],
    "IT": ["INFY","TCS","HCLTECH","WIPRO","TECHM"],
    "Auto": ["MARUTI","M&M","TATAMOTORS","HEROMOTOCO"],
    "Energy": ["RELIANCE","ONGC","IOC"],
    "FMCG": ["ITC","HINDUNILVR"]
}

sector = st.sidebar.selectbox("Sector", list(sector_map.keys()))
stocks = sector_map[sector]

timeframe = st.sidebar.selectbox("Timeframe", ["5m","15m","30m","1h"])
sl_pct = st.sidebar.slider("SL %",0.5,5.0,1.0)/100
tgt_pct = st.sidebar.slider("Target %",1.0,10.0,2.0)/100

# =============================
# DATA LOADER
# =============================
def load_data(stock):
    df = yf.download(stock+".NS", period="7d", interval=timeframe, progress=False)

    if df.empty:
        return df

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df.index = pd.to_datetime(df.index)

    try:
        df.index = df.index.tz_convert(None)
    except:
        pass

    return df.dropna()

# =============================
# SESSION FILTER
# =============================
def session_filter(df):
    if df.empty:
        return df
    return df[(df.index.time >= dtime(9,15)) & (df.index.time <= dtime(15,30))]

# =============================
# INDICATORS
# =============================
def indicators(df):
    df["EMA20"] = df["Close"].ewm(span=20).mean()
    df["EMA50"] = df["Close"].ewm(span=50).mean()
    df["VOL_AVG"] = df["Volume"].rolling(20).mean().fillna(0)

    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    rs = gain.rolling(14).mean()/(loss.rolling(14).mean()+1e-9)
    df["RSI"] = 100-(100/(1+rs))

    return df.fillna(0)

# =============================
# SIGNAL ENGINE (ALWAYS SIGNAL)
# =============================
def generate_signals(df, stock):
    df = indicators(df)
    signals = []

    for i in range(10, len(df)):
        row = df.iloc[i]
        price = row["Close"]

        # 🔥 Strong logic
        if row["EMA20"] > row["EMA50"] and row["RSI"] > 55:
            sig = "🟢 STRONG BUY"
        elif row["EMA20"] < row["EMA50"] and row["RSI"] < 45:
            sig = "🔴 STRONG SELL"

        # 🔥 Medium
        elif row["EMA20"] > row["EMA50"]:
            sig = "🟢 BUY"
        elif row["EMA20"] < row["EMA50"]:
            sig = "🔴 SELL"

        # 🔥 Fallback (never empty)
        else:
            sig = "🟢 WEAK BUY" if row["Close"] >= row["Open"] else "🔴 WEAK SELL"

        sl = price*(1-sl_pct) if "BUY" in sig else price*(1+sl_pct)
        tgt = price*(1+tgt_pct) if "BUY" in sig else price*(1-tgt_pct)

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
        df = load_data(s)
        df = session_filter(df)

        if not df.empty:
            all_signals += generate_signals(df, s)

    st.session_state.signals = all_signals

# =============================
# DISPLAY
# =============================
if "signals" in st.session_state:
    df = pd.DataFrame(st.session_state.signals)

    if not df.empty:
        df = df.sort_values("Time")
        df["Time"] = pd.to_datetime(df["Time"]).dt.strftime("%I:%M %p")

        st.dataframe(df, use_container_width=True)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["Time"], y=df["Price"], mode="lines+markers"))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No signals")

# =============================
# BACKTEST
# =============================
st.subheader("📊 BACKTEST")

bt_stock = st.selectbox("Stock", stocks)
bt_date = st.date_input("Date", datetime.now()-timedelta(days=1))

if st.button("RUN BACKTEST"):
    df = load_data(bt_stock)

    if df.empty:
        st.error("No Data")
        st.stop()

    df.index = pd.to_datetime(df.index)
    try:
        df.index = df.index.tz_convert(None)
    except:
        pass

    start = pd.Timestamp(bt_date)
    end = start + pd.Timedelta(days=1)

    day_df = df[(df.index >= start) & (df.index < end)]
    day_df = session_filter(day_df)

    st.write("📊 Candles:", len(day_df))

    if day_df.empty:
        st.error("No session data")
        st.stop()

    signals = generate_signals(day_df, bt_stock)
    res = pd.DataFrame(signals)

    res["Time"] = pd.to_datetime(res["Time"]).dt.strftime("%I:%M %p")
    st.dataframe(res, use_container_width=True)

    fig = go.Figure(data=[go.Candlestick(
        x=day_df.index,
        open=day_df["Open"],
        high=day_df["High"],
        low=day_df["Low"],
        close=day_df["Close"]
    )])

    fig.update_layout(xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
