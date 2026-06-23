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
st.set_page_config(page_title="NSE AI PRO V11.12", layout="wide", page_icon="🚀")

# 2. CORE FUNCTIONS
@st.cache_data(ttl=86400)
def load_nse500():
    try:
        import requests
        url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        df = pd.read_csv(io.StringIO(response.text))
        return sorted(df["Symbol"].dropna().unique().tolist())
    except: return ["RELIANCE", "TCS", "INFY", "HDFCBANK"]

@st.cache_data(ttl=120)
def get_data(symbol, interval, period):
    try:
        df = yf.download(f"{symbol}.NS", interval=interval, period=period, auto_adjust=True, progress=False)
        return df
    except: return pd.DataFrame()

def process_stock_thread(symbol, interval, period):
    df = get_data(symbol, interval, period)
    if df.empty or len(df) < 50: return None
    
    # Indicators
    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()
    tp = (df['High'] + df['Low'] + df['Close']) / 3
    df['VWAP'] = (df['Volume'] * tp).cumsum() / df['Volume'].cumsum()
    df["AVG_VOL"] = df["Volume"].rolling(20).mean()
    
    curr = df.iloc[-1]
    prev = df.iloc[-2]
    
    # News & VWAP Logic
    alerts = []
    rvol = curr['Volume'] / curr['AVG_VOL']
    gap_pct = ((curr['Open'] - prev['Close']) / prev['Close']) * 100
    
    if abs(gap_pct) >= 2.0 and rvol >= 2.0: alerts.append("📰 NEWS MOMENTUM")
    if abs(curr['Low'] - curr['VWAP']) / curr['VWAP'] <= 0.005 and curr['Close'] > curr['VWAP']: alerts.append("💧 VWAP Bounce")
    
    return [
        symbol, round(curr['Close'], 2), round(gap_pct, 2), 
        round(curr['VWAP'], 2), round(rvol, 2), ", ".join(alerts)
    ]

# 3. UI
st.title("🚀 NSE AI PRO V11.12 - Institutional Ultimate")

if st.button("🚀 RUN ULTIMATE SCANNER"):
    stocks = load_nse500()
    results = []
    
    progress = st.progress(0)
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(process_stock_thread, s, "15m", "5d"): s for s in stocks}
        for i, future in enumerate(as_completed(futures)):
            res = future.result()
            if res: results.append(res)
            progress.progress((i + 1) / len(stocks))
            
    df_res = pd.DataFrame(results, columns=["Stock", "LTP", "Gap %", "VWAP", "RVOL", "Alerts"])
    st.session_state.v11_master_data = df_res

if not st.session_state.v11_master_data.empty:
    st.dataframe(st.session_state.v11_master_data, use_container_width=True)
    
    # Download
    csv = st.session_state.v11_master_data.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Master Report", csv, "NSE_AI_PRO_Report.csv", "text/csv")
