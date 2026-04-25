import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
import os

# =============================
# 1. CONFIG (ఎర్రర్ రాకుండా జాగ్రత్తలు తీసుకున్నాను)
# =============================
st.set_page_config(page_title="NSE AI PRO V22", layout="wide")

st.title("🚀 NSE AI PRO V22 - Smart Money Terminal")
st.write("Big Player ఎంట్రీలను మరియు రివర్సల్స్ ని గుర్తించే అధునాతన సిస్టమ్.")

# ఆటో రిఫ్రెష్ - ప్రతి 1 నిమిషానికి
st_autorefresh(interval=60000, key="refresh")

# బ్యాక్‌టెస్ట్ ఫోల్డర్
BACKTEST_DIR = "backtests_v22"
if not os.path.exists(BACKTEST_DIR):
    os.makedirs(BACKTEST_DIR)

# =============================
# 2. SECTOR MAP
# =============================
sector_map = {
    "Banking": ["HDFCBANK", "ICICIBANK", "SBIN", "AXISBANK", "KOTAKBANK"],
    "IT": ["INFY", "TCS", "HCLTECH", "WIPRO", "TECHM"],
    "Auto": ["MARUTI", "M&M", "TATAMOTORS", "HEROMOTOCO"],
    "Oil & Metals": ["RELIANCE", "ONGC", "TATASTEEL", "HINDALCO"]
}

st.sidebar.header("Settings")
sector = st.sidebar.selectbox("📂 Sector", list(sector_map.keys()))
stocks = sector_map[sector]
timeframe = st.sidebar.selectbox("⏱️ Interval", ["5m", "15m", "30m", "1h"])

# =============================
# 3. DATA & INDICATORS
# =============================
@st.cache_data(ttl=60)
def load_data(stock, interval):
    df = yf.Ticker(stock + ".NS").history(period="5d", interval=interval)
    return df

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
    
    # Volume Analysis
    df['AvgVol'] = df['Volume'].rolling(20).mean()
    return df

# =============================
# 4. BIG PLAYER & REVERSAL LOGIC
# =============================
def get_signals(df, stock):
    df = apply_indicators(df)
    signals = []
    
    for i in range(30, len(df)):
        row = df.iloc[i]
        prev_row = df.iloc[i-1]
        
        # A. BIG PLAYER DETECTION (వాల్యూమ్ 2.5 రెట్లు పెరిగితే)
        if row['Volume'] > (row['AvgVol'] * 2.5):
            s_type = "🔥 BIG BUY" if row['Close'] > row['Open'] else "💀 BIG SELL"
            signals.append({"Stock": stock, "Type": s_type, "Price": round(row['Close'],2), "Time": df.index[i]})
        
        # B. BULLISH REVERSAL
        elif prev_row['Close'] < row['EMA20'] and row['Close'] > row['EMA20'] and row['RSI'] > 40:
            if row['EMA20'] > row['EMA50']:
                signals.append({"Stock": stock, "Type": "🟢 Bullish", "Price": round(row['Close'],2), "Time": df.index[i]})

        # C. BEARISH REVERSAL
        elif prev_row['Close'] > row['EMA20'] and row['Close'] < row['EMA20'] and row['RSI'] < 60:
            if row['EMA20'] < row['EMA50']:
                signals.append({"Stock": stock, "Type": "🔴 Bearish", "Price": round(row['Close'],2), "Time": df.index[i]})
                
    return signals

# =============================
# 5. UI & DISPLAY
# =============================
if st.button("🚀 SCAN FOR BIG PLAYERS"):
    results = []
    for s in stocks:
        data = load_data(s, timeframe)
        if not data.empty:
            sigs = get_signals(data, s)
            results.extend(sigs)
    st.session_state.v22_data = results

if "v22_data" in st.session_state and st.session_state.v22_data:
    df_res = pd.DataFrame(st.session_state.v22_data)
    df_res["Time"] = pd.to_datetime(df_res["Time"]).dt.strftime("%I:%M %p")
    
    st.subheader("🎯 Market Intelligence Signals")
    st.dataframe(df_res.sort_values(by="Time", ascending=False), use_container_width=True)

    # Chart Section
    selected_s = st.selectbox("📊 View Chart", stocks)
    c_data = load_data(selected_s, timeframe)
    c_data = apply_indicators(c_data)
    
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=c_data.index, open=c_data['Open'], high=c_data['High'], low=c_data['Low'], close=c_data['Close'], name="Price"))
    fig.add_trace(go.Scatter(x=c_data.index, y=c_data['EMA200'], name="EMA 200", line=dict(color='red')))
    fig.add_trace(go.Scatter(x=c_data.index, y=c_data['VWAP'], name="VWAP", line=dict(color='orange', dash='dash')))
    
    fig.update_layout(height=600, template="plotly_dark", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

# =============================
# 6. BACKTEST
# =============================
if st.sidebar.checkbox("📊 Backtest History"):
    st.divider()
    bt_date = st.sidebar.date_input("Select Date", datetime.now() - timedelta(1))
    st.write(f"Backtesting {sector} stocks for {bt_date}...")
    
    # Simple Backtest Display
    # Note: Full backtest logic can be expanded here
    st.info("గత డేటా ఆధారంగా బిగ్ ప్లేయర్ ఎంట్రీలను ఇక్కడ విశ్లేషించవచ్చు.")
