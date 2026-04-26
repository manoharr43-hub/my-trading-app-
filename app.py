import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
import os

# =============================
# 1. CONFIG
# =============================
st.set_page_config(page_title="NSE AI PRO V22.1", layout="wide")
st.title("🚀 NSE AI PRO V22.1 - Smart Money (with SL/Target)")

st_autorefresh(interval=60000, key="refresh")

# =============================
# 2. SECTOR & SETTINGS
# =============================
sector_map = {
    "Banking": ["HDFCBANK", "ICICIBANK", "SBIN", "AXISBANK", "KOTAKBANK"],
    "IT": ["INFY", "TCS", "HCLTECH", "WIPRO", "TECHM"],
    "Auto": ["MARUTI", "M&M", "TATAMOTORS", "HEROMOTOCO"],
    "Oil & Metals": ["RELIANCE", "ONGC", "TATASTEEL", "HINDALCO"]
}

st.sidebar.header("⚙️ Strategy Settings")
sector = st.sidebar.selectbox("📂 Sector", list(sector_map.keys()))
stocks = sector_map[sector]
timeframe = st.sidebar.selectbox("⏱️ Interval", ["5m", "15m", "30m", "1h"])

# SL & Target Percentages (మీరు ఇక్కడ మార్చుకోవచ్చు)
sl_pct = st.sidebar.slider("Stop Loss (%)", 0.5, 5.0, 1.0) / 100
tgt_pct = st.sidebar.slider("Target (%)", 1.0, 10.0, 2.0) / 100

# =============================
# 3. DATA ENGINE
# =============================
@st.cache_data(ttl=60)
def load_data(stock, interval, period="5d"):
    df = yf.Ticker(stock + ".NS").history(period=period, interval=interval)
    return df

def apply_indicators(df):
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
# 4. SIGNAL LOGIC WITH SL/TGT
# =============================
def get_signals(df, stock):
    df = apply_indicators(df)
    signals = []
    
    for i in range(30, len(df)):
        row = df.iloc[i]
        prev_row = df.iloc[i-1]
        price = round(row['Close'], 2)
        
        sig_type = None
        
        # A. Big Player Check
        if row['Volume'] > (row['AvgVol'] * 2.5):
            sig_type = "🔥 BIG BUY" if row['Close'] > row['Open'] else "💀 BIG SELL"
        
        # B. Reversal Check
        elif prev_row['Close'] < row['EMA20'] and row['Close'] > row['EMA20'] and row['RSI'] > 40:
            if row['EMA20'] > row['EMA50']: sig_type = "🟢 Bullish"
            
        elif prev_row['Close'] > row['EMA20'] and row['Close'] < row['EMA20'] and row['RSI'] < 60:
            if row['EMA20'] < row['EMA50']: sig_type = "🔴 Bearish"

        if sig_type:
            # Entry, SL, Target Calculations
            if "BUY" in sig_type or "Bullish" in sig_type:
                sl = round(price * (1 - sl_pct), 2)
                tgt = round(price * (1 + tgt_pct), 2)
            else:
                sl = round(price * (1 + sl_pct), 2)
                tgt = round(price * (1 - tgt_pct), 2)
                
            signals.append({
                "Stock": stock,
                "Type": sig_type,
                "Entry": price,
                "StopLoss": sl,
                "Target": tgt,
                "Time": df.index[i]
            })
                
    return signals

# =============================
# 5. UI DISPLAY
# =============================
if st.button("🚀 SCAN FOR TRADES"):
    results = []
    for s in stocks:
        data = load_data(s, timeframe)
        if not data.empty:
            sigs = get_signals(data, s)
            results.extend(sigs)
    st.session_state.v22_data = results

if "v22_data" in st.session_state and st.session_state.v22_data:
    df_res = pd.DataFrame(st.session_state.v22_data)
    # Time Formatting
    df_res["Time"] = pd.to_datetime(df_res["Time"]).dt.strftime("%d-%m %I:%M %p")
    
    st.subheader("🎯 Trade Setup (Entry, SL, Target)")
    st.dataframe(df_res.sort_values(by="Time", ascending=False), use_container_width=True)

# =============================
# 6. BACKTEST (FIXED)
# =============================
st.divider()
st.subheader("📊 Backtest Section")
col1, col2 = st.columns([1, 3])

with col1:
    bt_stock = st.selectbox("Select Stock for Backtest", stocks)
    bt_date = st.date_input("Select Backtest Date", datetime.now() - timedelta(1))

if st.button("🔍 Run Backtest"):
    # బ్యాక్ టెస్ట్ కోసం కనీసం 30 రోజుల డేటా కావాలి (ఇండికేటర్స్ కాలిక్యులేషన్ కోసం)
    bt_data_all = load_data(bt_stock, timeframe, period="1mo")
    
    # ఎంచుకున్న తేదీ డేటాను ఫిల్టర్ చేయడం
    bt_data = bt_data_all[bt_data_all.index.date == bt_date]
    
    if not bt_data.empty:
        # సిగ్నల్స్ ని ఎంచుకున్న డేటా నుండి కాకుండా, ఫుల్ డేటా నుండి తీసి ఫిల్టర్ చేయాలి
        all_sigs = get_signals(bt_data_all, bt_stock)
        day_sigs = [s for s in all_sigs if s['Time'].date() == bt_date]
        
        if day_sigs:
            st.success(f"Found {len(day_sigs)} signals on {bt_date}")
            bt_df = pd.DataFrame(day_sigs)
            bt_df["Time"] = pd.to_datetime(bt_df["Time"]).dt.strftime("%I:%M %p")
            st.table(bt_df[["Type", "Entry", "StopLoss", "Target", "Time"]])
            
            # Chart
            fig_bt = go.Figure(data=[go.Candlestick(x=bt_data.index, open=bt_data['Open'], high=bt_data['High'], low=bt_data['Low'], close=bt_data['Close'])])
            fig_bt.update_layout(title=f"{bt_stock} Chart - {bt_date}", template="plotly_dark", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig_bt, use_container_width=True)
        else:
            st.warning("No signals found for this date.")
    else:
        st.error("Data not available for this date. Please check if it was a market holiday.")
