import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
import os

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V21 HQ", layout="wide")
st.title("🚀 NSE AI PRO V21 - High Quality Trade System (Reversal Detection)")

st_autorefresh(interval=60000, key="refresh")

# =============================
# BACKTEST FOLDER
# =============================
BACKTEST_DIR = "backtests"
os.makedirs(BACKTEST_DIR, exist_ok=True)

# =============================
# SESSION
# =============================
if "signals" not in st.session_state:
    st.session_state.signals = []

# =============================
# SECTOR MAP
# =============================
sector_map = {
    "Banking": ["HDFCBANK","ICICIBANK","SBIN","AXISBANK","KOTAKBANK"],
    "IT": ["INFY","TCS","HCLTECH","WIPRO","TECHM"],
    "Auto": ["MARUTI","M&M","TATAMOTORS","HEROMOTOCO"],
    "FMCG": ["ITC","HINDUNILVR","NESTLEIND"],
    "Oil": ["RELIANCE","ONGC","BPCL"],
    "Metals": ["TATASTEEL","JSWSTEEL","HINDALCO"],
}

sector = st.sidebar.selectbox("📂 Sector", list(sector_map.keys()))
stocks = sector_map[sector]

# =============================
# DATA
# =============================
@st.cache_data(ttl=60)
def load_data(stock, interval="5m", period="5d"):
    df = yf.Ticker(stock + ".NS").history(period=period, interval=interval)
    return df

# =============================
# INDICATORS
# =============================
def indicators(df):
    df = df.copy()
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    df['EMA200'] = df['Close'].ewm(span=200).mean()
    tp = (df['High'] + df['Low'] + df['Close']) / 3
    df['VWAP'] = (tp * df['Volume']).cumsum() / df['Volume'].cumsum()
    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    rs = gain.rolling(14).mean() / (loss.rolling(14).mean() + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))
    df['AvgVol'] = df['Volume'].rolling(20).mean()
    return df

# =============================
# REVERSAL DETECTION
# =============================
def detect_reversal(df, stock):
    df = indicators(df)
    signals = []
    for i in range(50, len(df)):
        price = df['Close'].iloc[i]
        prev_price = df['Close'].iloc[i-1]
        rsi = df['RSI'].iloc[i]
        ema20 = df['EMA20'].iloc[i]
        ema50 = df['EMA50'].iloc[i]
        ema200 = df['EMA200'].iloc[i]

        if prev_price < ema20 and price > ema20 and rsi > 35 and ema20 > ema50:
            signals.append({"Stock":stock,"Type":"Bullish Reversal","Price":price,"Time":df.index[i]})

        elif prev_price > ema20 and price < ema20 and rsi < 65 and ema20 < ema50:
            signals.append({"Stock":stock,"Type":"Bearish Reversal","Price":price,"Time":df.index[i]})

    return signals[-10:]

# =============================
# LIVE SYSTEM
# =============================
if st.button("🚀 START HQ LIVE TRADING"):
    all_signals = []
    for s in stocks:
        df = load_data(s, "5m", "5d")
        signals = detect_reversal(df, s)
        all_signals.extend(signals)
    st.session_state.signals = all_signals

# =============================
# DISPLAY + LIVE CHART
# =============================
if st.session_state.signals:
    df_sig = pd.DataFrame(st.session_state.signals)
    df_sig["Time"] = pd.to_datetime(df_sig["Time"]).dt.strftime("%I:%M %p")
    df_sig = df_sig.sort_values(by="Time").reset_index(drop=True)

    st.subheader("🔄 Reversal Detection Signals")
    st.dataframe(df_sig[["Stock","Type","Price","Time"]])

    stock = st.selectbox("📊 Chart", stocks)
    df_chart = load_data(stock, "5m", "5d")   # 👉 LIVE chart కూడా 5m intervalలో ఉండాలి

    if not df_chart.empty:
        fig = go.Figure(data=[go.Candlestick(
            x=df_chart.index,
            open=df_chart['Open'],
            high=df_chart['High'],
            low=df_chart['Low'],
            close=df_chart['Close']
        )])

        df_s = df_sig[df_sig["Stock"]==stock]
        if not df_s.empty:
            for _, r in df_s.iterrows():
                fig.add_trace(go.Scatter(
                    x=[r["Time"]],
                    y=[r["Price"]],
                    mode="markers",
                    marker=dict(size=12, color="blue" if "Bullish" in r["Type"] else "orange"),
                    name=r["Type"]
                ))

        fig.update_layout(title=f"{stock} - Live Reversal Chart", 
                          xaxis_title="Time", yaxis_title="Price")
        st.plotly_chart(fig, use_container_width=True)

# =============================
# BACKTEST
# =============================
if st.checkbox("📊 BACKTEST MODE"):
    date = st.date_input("Select Date", datetime.now().date() - timedelta(days=1))
    bt_all = []

    for s in stocks:
        df = yf.Ticker(s + ".NS").history(period="5d", interval="5m")
        df = df[df.index.date == date]

        if not df.empty:
            signals = detect_reversal(df, s)
            bt_all.extend(signals)

            # Save signals to CSV in backtest folder
            if signals:
                df_save = pd.DataFrame(signals)
                filename = f"{BACKTEST_DIR}/backtest_{s}_{date}.csv"
                df_save.to_csv(filename, index=False)

            fig_bt = go.Figure(data=[go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close']
            )])

            df_s = pd.DataFrame(signals)
            if not df_s.empty:
                for _, r in df_s.iterrows():
                    fig_bt.add_trace(go.Scatter(
                        x=[r["Time"]],
                        y=[r["Price"]],
                        mode="markers",
                        marker=dict(size=12, color="blue" if "Bullish" in r["Type"] else "orange"),
                        name=f"{s} {r['Type']}"
                    ))

            fig_bt.update_layout(title=f"{s} - Backtest Reversal Chart ({date})",
                                 xaxis_title="Time", yaxis_title="Price")
            st.plotly_chart(fig_bt, use_container_width=True)

    st.subheader("📊 BACKTEST RESULTS")
    if bt_all:
        df_bt = pd.DataFrame(bt_all)
        df_bt["Time"] = pd.to_datetime(df_bt["Time"]).dt.strftime("%I:%M %p")
        df_bt = df_bt.sort_values(by="Time").reset_index(drop=True)
        st.dataframe(df_bt[["Stock","Type","Price","Time"]])
    else:
        st.warning("No signals found for selected date")

# =============================
# BACKTEST FOLDER DISPLAY
# =============================
st.sidebar.subheader("📂 Backtest Folder Contents")
files = os.listdir(BACKTEST_DIR)
if files:
    for f in files:
        st.sidebar.write(f)
else:
    st.sidebar.write("No backtest files yet")
