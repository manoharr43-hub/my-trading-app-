import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
import os

# =============================
# CONFIG & STYLE
# =============================
st.set_page_config(page_title="🚀 NSE AI PRO V22 - SMART MONEY", layout="wide")
st.markdown("""
    <style>
    .big-font { font-size:20px !important; font-weight: bold; color: #ff4b4b; }
    .stDataFrame { border: 1px solid #444; }
    </style>
    """, unsafe_allow_index=True)

st.title("🚀 NSE AI PRO V22 - Big Player & Reversal Terminal")
st_autorefresh(interval=60000, key="refresh")

# =============================
# DIRECTORY SETUP
# =============================
BACKTEST_DIR = "backtests_v22"
os.makedirs(BACKTEST_DIR, exist_ok=True)

# =============================
# SECTOR MAP
# =============================
sector_map = {
    "Banking": ["HDFCBANK", "ICICIBANK", "SBIN", "AXISBANK", "KOTAKBANK"],
    "IT": ["INFY", "TCS", "HCLTECH", "WIPRO", "TECHM"],
    "Auto": ["MARUTI", "M&M", "TATAMOTORS", "HEROMOTOCO", "BAJAJ-AUTO"],
    "FMCG": ["ITC", "HINDUNILVR", "NESTLEIND", "BRITANNIA"],
    "Oil & Metals": ["RELIANCE", "ONGC", "TATASTEEL", "JINDALSTEL"]
}

sector = st.sidebar.selectbox("📂 Select Sector", list(sector_map.keys()))
stocks = sector_map[sector]
timeframe = st.sidebar.selectbox("⏱️ Timeframe", ["5m", "15m", "30m", "1h"], index=0)

# =============================
# DATA ENGINE
# =============================
@st.cache_data(ttl=60)
def load_data(stock, interval, period="5d"):
    df = yf.Ticker(stock + ".NS").history(period=period, interval=interval)
    return df

# =============================
# ADVANCED INDICATORS
# =============================
def apply_indicators(df):
    df = df.copy()
    # EMAs
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    df['EMA200'] = df['Close'].ewm(span=200).mean()
    
    # VWAP
    tp = (df['High'] + df['Low'] + df['Close']) / 3
    df['VWAP'] = (tp * df['Volume']).cumsum() / df['Volume'].cumsum()
    
    # RSI
    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    rs = gain.rolling(14).mean() / (loss.rolling(14).mean() + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Volume Metrics for Big Player Detection
    df['AvgVol'] = df['Volume'].rolling(20).mean()
    df['Vol_Shock'] = df['Volume'] / df['AvgVol']
    
    return df

# =============================
# SMART SIGNAL ENGINE
# =============================
def detect_signals(df, stock):
    df = apply_indicators(df)
    signals = []
    
    for i in range(50, len(df)):
        row = df.iloc[i]
        prev_row = df.iloc[i-1]
        
        # 1. BIG PLAYER ENTRY (High Volume + Large Candle)
        body_size = abs(row['Close'] - row['Open'])
        avg_body = abs(df['Close'] - df['Open']).rolling(20).mean().iloc[i]
        
        if row['Vol_Shock'] > 2.5 and body_size > (avg_body * 2):
            sig_type = "🔥 BIG PLAYER BUY" if row['Close'] > row['Open'] else "💀 BIG PLAYER SELL"
            signals.append({"Stock": stock, "Type": sig_type, "Price": round(row['Close'],2), "Time": df.index[i]})

        # 2. REVERSAL LOGIC (Your Existing logic refined)
        elif prev_row['Close'] < row['EMA20'] and row['Close'] > row['EMA20'] and row['RSI'] > 40:
            if row['EMA20'] > row['EMA50']:
                signals.append({"Stock": stock, "Type": "🟢 Bullish Reversal", "Price": round(row['Close'],2), "Time": df.index[i]})

        elif prev_row['Close'] > row['EMA20'] and row['Close'] < row['EMA20'] and row['RSI'] < 60:
            if row['EMA20'] < row['EMA50']:
                signals.append({"Stock": stock, "Type": "🔴 Bearish Reversal", "Price": round(row['Close'],2), "Time": df.index[i]})

    return signals

# =============================
# MAIN UI
# =============================
if st.button("🚀 SCAN MARKET FOR BIG PLAYERS"):
    all_found = []
    with st.spinner("Analyzing Institutional Data..."):
        for s in stocks:
            data = load_data(s, timeframe)
            if not data.empty:
                s_list = detect_signals(data, s)
                all_found.extend(s_list)
    
    st.session_state.v22_signals = all_found

# DISPLAY SIGNALS
if "v22_signals" in st.session_state and st.session_state.v22_signals:
    df_sig = pd.DataFrame(st.session_state.v22_signals)
    df_sig["Time"] = pd.to_datetime(df_sig["Time"]).dt.strftime("%Y-%m-%d %I:%M %p")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("🎯 Trade Alerts")
        st.dataframe(df_sig.sort_values(by="Time", ascending=False), height=400)
    
    with col2:
        selected_stock = st.selectbox("🔍 Visual Chart Analysis", stocks)
        chart_data = load_data(selected_stock, timeframe)
        chart_data = apply_indicators(chart_data)
        
        fig = go.Figure()
        # Candlestick
        fig.add_trace(go.Candlestick(x=chart_data.index, open=chart_data['Open'], 
                                     high=chart_data['High'], low=chart_data['Low'], 
                                     close=chart_data['Close'], name="Price"))
        # Indicators
        fig.add_trace(go.Scatter(x=chart_data.index, y=chart_data['EMA200'], name="EMA 200", line=dict(color='red', width=2)))
        fig.add_trace(go.Scatter(x=chart_data.index, y=chart_data['VWAP'], name="VWAP", line=dict(color='orange', dash='dash')))

        # Highlight Signals on Chart
        stock_sigs = df_sig[df_sig["Stock"] == selected_stock]
        for _, s in stock_sigs.iterrows():
            color = "yellow" if "BIG PLAYER" in s["Type"] else ("green" if "Bullish" in s["Type"] else "red")
            fig.add_annotation(x=s["Time"], y=s["Price"], text=s["Type"], showarrow=True, arrowhead=1, bgcolor=color)

        fig.update_layout(height=600, template="plotly_dark", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

# =============================
# BACKTESTING SECTION
# =============================
st.divider()
if st.checkbox("📊 Run Strategy Backtest"):
    bt_date = st.date_input("Select History Date", datetime.now() - timedelta(1))
    st.info(f"Analyzing {selected_stock} for {bt_date}...")
    
    # Fetch more data to ensure we have the selected date
    bt_data = yf.Ticker(selected_stock + ".NS").history(period="1mo", interval=timeframe)
    target_data = bt_data[bt_data.index.date == bt_date]
    
    if not target_data.empty:
        results = detect_signals(target_data, selected_stock)
        if results:
            st.success(f"Found {len(results)} signals on {bt_date}")
            st.table(pd.DataFrame(results))
        else:
            st.warning("No institutional activity detected on this date.")
    else:
        st.error("No data available for the selected date.")
