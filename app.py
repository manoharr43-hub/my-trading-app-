import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import io
import time
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
from xgboost import XGBClassifier
import warnings

warnings.filterwarnings('ignore')

# 1. PAGE SETUP
st.set_page_config(page_title="NSE AI PRO V11.10", layout="wide", page_icon="🚀")

st.title("🚀 NSE AI PRO V11.10 - Institutional Ultimate")
st.markdown("**News Momentum | VWAP Bounce | SMC/CISD | XGBoost AI**")

# Session State
if 'v11_master_data' not in st.session_state:
    st.session_state.v11_master_data = pd.DataFrame()

# 2. CORE FUNCTIONS
@st.cache_data(ttl=3600)
def get_data(symbol, interval, period):
    try:
        df = yf.download(f"{symbol}.NS", interval=interval, period=period, progress=False, auto_adjust=True)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        return df
    except: return pd.DataFrame()

def add_indicators(df):
    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()
    tp = (df['High'] + df['Low'] + df['Close']) / 3
    df['VWAP'] = (df['Volume'] * tp).cumsum() / df['Volume'].cumsum()
    df["AVG_VOL"] = df["Volume"].rolling(20).mean()
    return df

def process_stock(symbol, interval, period):
    df = get_data(symbol, interval, period)
    if df.empty or len(df) < 50: return None
    df = add_indicators(df)
    
    close = float(df["Close"].iloc[-1])
    vwap = float(df["VWAP"].iloc[-1])
    rvol = float(df["Volume"].iloc[-1] / df["AVG_VOL"].iloc[-1])
    
    # News & VWAP Logic
    alerts = []
    gap_pct = ((df['Open'].iloc[-1] - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
    if abs(gap_pct) >= 2.0 and rvol >= 2.0: alerts.append("📰 NEWS MOMENTUM")
    if abs(df["Low"].iloc[-1] - vwap) / vwap <= 0.005 and close > vwap: alerts.append("💧 VWAP Bounce")
    
    return [symbol, round(close, 2), round(vwap, 2), round(rvol, 2), ", ".join(alerts)]

# 3. UI & RUN
if st.button("🚀 RUN ULTIMATE SCANNER"):
    stocks = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "SBIN", "TATAMOTORS"]
    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(process_stock, s, "15m", "5d"): s for s in stocks}
        for future in as_completed(futures):
            res = future.result()
            if res: results.append(res)
            
    df_res = pd.DataFrame(results, columns=["Stock", "LTP", "VWAP", "RVOL", "Alerts"])
    st.session_state.v11_master_data = df_res

if not st.session_state.v11_master_data.empty:
    st.dataframe(st.session_state.v11_master_data, use_container_width=True)
    
    # Download Button
    csv = st.session_state.v11_master_data.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Report", csv, "report.csv", "text/csv")
