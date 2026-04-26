import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# =============================
# APP CONFIG
# =============================
st.set_page_config(page_title="NSE AI PRO V23", layout="wide")
st.title("🚀 NSE AI PRO V23 - Smart Money + FIXED BACKTEST")

st_autorefresh(interval=60000, key="refresh")

# =============================
# SECTORS
# =============================
sector_map = {
    "Banking": ["HDFCBANK", "ICICIBANK", "SBIN", "AXISBANK", "KOTAKBANK"],
    "IT": ["INFY", "TCS", "HCLTECH", "WIPRO", "TECHM"],
    "Auto": ["MARUTI", "M&M", "TATAMOTORS", "HEROMOTOCO"],
    "Oil": ["RELIANCE", "ONGC", "TATASTEEL", "HINDALCO"]
}

st.sidebar.header("⚙️ Settings")
sector = st.sidebar.selectbox("Sector", list(sector_map.keys()))
stocks = sector_map[sector]
timeframe = st.sidebar.selectbox("Interval", ["5m", "15m", "30m", "1h"])

sl_pct = st.sidebar.slider("SL %", 0.5, 5.0, 1.0) / 100
tgt_pct = st.sidebar.slider("Target %", 1.0, 10.0, 2.0) / 100

# =============================
# DATA LOADER
# =============================
@st.cache_data(ttl=60)
def load_data(stock, interval, period="5d"):
    df = yf.Ticker(stock + ".NS").history(period=period, interval=interval)
    return df

# =============================
# INDICATORS
# =============================
def add_indicators(df):
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
# SIGNAL ENGINE
# =============================
def generate_signals(df, stock):
    df = add_indicators(df)
    signals = []

    for i in range(30, len(df)):
        row = df.iloc[i]
        prev = df.iloc[i - 1]

        price = round(row["Close"], 2)
        sig = None

        # Big money
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
                sl = price * (1 - sl_pct)
                tgt = price * (1 + tgt_pct)
            else:
                sl = price * (1 + sl_pct)
                tgt = price * (1 - tgt_pct)

            signals.append({
                "Stock": stock,
                "Type": sig,
                "Entry": price,
                "SL": round(sl, 2),
                "Target": round(tgt, 2),
                "Time": df.index[i]
            })

    return signals

# =============================
# LIVE SCAN
# =============================
if st.button("🚀 SCAN MARKET"):
    all_results = []

    for s in stocks:
        data = load_data(s, timeframe)
        if not data.empty:
            all_results.extend(generate_signals(data, s))

    st.session_state.results = all_results

if "results" in st.session_state:
    df = pd.DataFrame(st.session_state.results)

    if not df.empty:
        df["Time"] = pd.to_datetime(df["Time"]).dt.strftime("%d-%m %H:%M")
        st.subheader("📊 LIVE SIGNALS")
        st.dataframe(df, use_container_width=True)

# =============================
# BACKTEST (FULL FIXED)
# =============================
st.divider()
st.subheader("📊 BACKTEST ENGINE")

col1, col2 = st.columns([1, 3])

with col1:
    bt_stock = st.selectbox("Stock", stocks, key="bt")
    bt_date = st.date_input("Date", datetime.now() - timedelta(days=1))

if st.button("🔍 RUN BACKTEST"):

    df = load_data(bt_stock, timeframe, period="2mo")

    if df.empty:
        st.error("No data")
        st.stop()

    df = df.copy()
    df.index = pd.to_datetime(df.index)

    df["date"] = df.index.date
    day_df = df[df["date"] == bt_date]

    # ================= CHART =================
    fig = go.Figure()

    if not day_df.empty:
        fig.add_trace(go.Candlestick(
            x=day_df.index,
            open=day_df["Open"],
            high=day_df["High"],
            low=day_df["Low"],
            close=day_df["Close"]
        ))
    else:
        st.warning("No chart data for selected date")

    fig.update_layout(
        title=f"{bt_stock} - {bt_date}",
        template="plotly_dark",
        xaxis_rangeslider_visible=False
    )

    st.plotly_chart(fig, use_container_width=True)

    # ================= SIGNALS =================
    full_signals = generate_signals(df.drop(columns=["date"]), bt_stock)

    day_signals = []
    for s in full_signals:
        try:
            if pd.to_datetime(s["Time"]).date() == bt_date:
                day_signals.append(s)
        except:
            pass

    if day_signals:
        st.success(f"{len(day_signals)} signals found")

        bt_df = pd.DataFrame(day_signals)
        bt_df["Time"] = pd.to_datetime(bt_df["Time"]).dt.strftime("%H:%M")

        st.dataframe(bt_df[["Type", "Entry", "SL", "Target", "Time"]])
    else:
        st.info("No signals for this date")
