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
st.set_page_config(page_title="NSE AI PRO V23.2", layout="wide")
st.title("🚀 NSE AI PRO V23.2 - ZERO ERROR STABLE SYSTEM")

# ప్రతి 60 సెకన్లకు యాప్ ఆటోమేటిక్‌గా రిఫ్రెష్ అవుతుంది
st_autorefresh(interval=60000, key="refresh")

# =============================
# STOCK LIST
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

sl_pct = st.sidebar.slider("Stop Loss %", 0.5, 5.0, 1.0) / 100
tgt_pct = st.sidebar.slider("Target %", 1.0, 10.0, 2.0) / 100

# =============================
# DATA LOADER SAFE
# =============================
@st.cache_data(ttl=60)
def load_data(stock, interval, period="5d"):
    try:
        df = yf.Ticker(stock + ".NS").history(period=period, interval=interval)
        return df
    except Exception as e:
        st.error(f"Error loading {stock}: {e}")
        return pd.DataFrame()

# =============================
# INDICATORS
# =============================
def add_indicators(df):
    df = df.copy()
    if len(df) < 50: return df

    df["EMA20"] = df["Close"].ewm(span=20).mean()
    df["EMA50"] = df["Close"].ewm(span=50).mean()

    tp = (df["High"] + df["Low"] + df["Close"]) / 3
    df["VWAP"] = (tp * df["Volume"]).cumsum() / (df["Volume"].cumsum() + 1e-9)

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
def get_signals(df, stock):
    df = add_indicators(df)
    signals = []
    if df.empty or "EMA20" not in df.columns: return signals

    for i in range(30, len(df)):
        row = df.iloc[i]
        prev = df.iloc[i - 1]
        price = float(row["Close"])
        sig = None

        # Logic 1: Volume Blast
        if row["Volume"] > row["AvgVol"] * 2.5:
            sig = "🔥 BIG BUY" if row["Close"] > row["Open"] else "💀 BIG SELL"

        # Logic 2: EMA Crossover Bullish
        elif prev["Close"] < row["EMA20"] and row["Close"] > row["EMA20"] and row["RSI"] > 40:
            if row["EMA20"] > row["EMA50"]:
                sig = "🟢 BULLISH"

        # Logic 3: EMA Crossover Bearish
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
                "Entry": round(price, 2),
                "SL": round(sl, 2),
                "Target": round(tgt, 2),
                "Time": df.index[i]
            })
    return signals

# =============================
# LIVE SCAN SECTION
# =============================
if st.button("🚀 SCAN MARKET"):
    all_data = []
    for s in stocks:
        df = load_data(s, timeframe)
        if not df.empty:
            all_data.extend(get_signals(df, s))
    st.session_state.results = all_data

if "results" in st.session_state:
    res_df = pd.DataFrame(st.session_state.results)
    if not res_df.empty:
        res_df["Time"] = pd.to_datetime(res_df["Time"]).dt.strftime("%d-%m %H:%M")
        st.subheader("📊 LIVE SIGNALS")
        st.dataframe(res_df, use_container_width=True)
    else:
        st.info("ప్రస్తుతానికి ఎటువంటి సిగ్నల్స్ లేవు.")

# =============================
# BACKTEST ENGINE (FIXED)
# =============================
st.divider()
st.subheader("📊 BACKTEST ENGINE")

col1, col2 = st.columns([1, 3])

with col1:
    bt_stock = st.selectbox("Select Stock", stocks, key="bt_stock_select")
    # మునుపటి ఎర్రర్ ఇక్కడ సరిచేయబడింది
    bt_date = st.date_input("Analysis Date", datetime.now() - timedelta(days=1))

with col2:
    bt_df = load_data(bt_stock, timeframe, period="5d")
    if not bt_df.empty:
        bt_df_ind = add_indicators(bt_df)
        
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=bt_df.index, open=bt_df['Open'], high=bt_df['High'],
            low=bt_df['Low'], close=bt_df['Close'], name="Market Data"
        ))
        
        if "EMA20" in bt_df_ind.columns:
            fig.add_trace(go.Scatter(x=bt_df_ind.index, y=bt_df_ind['EMA20'], name="EMA20", line=dict(color='orange')))
            fig.add_trace(go.Scatter(x=bt_df_ind.index, y=bt_df_ind['EMA50'], name="EMA50", line=dict(color='blue')))
        
        fig.update_layout(height=500, xaxis_rangeslider_visible=False, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("బ్యాక్‌టెస్ట్ చేయడానికి డేటా అందుబాటులో లేదు.")
