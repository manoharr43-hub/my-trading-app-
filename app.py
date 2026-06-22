import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import io
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed

warnings.filterwarnings("ignore")

# PAGE CONFIG
st.set_page_config(page_title="NSE AI PRO", layout="wide", page_icon="🚀")
st.title("🚀 NSE AI PRO V11.15 - Stable Cloud Edition")

# SIDEBAR
with st.sidebar:
    symbols = st.text_area("Enter Stock Symbols (Comma Separated)", "RELIANCE, TCS, INFY, HDFCBANK, SBIN, TATAMOTORS")
    run_scanner = st.button("🚀 RUN SCANNER")

# DATA ENGINE
def get_data(symbol):
    try:
        df = yf.download(f"{symbol}.NS", period="3mo", interval="15m", progress=False, threads=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        # Indicators
        df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
        df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()
        df["RSI"] = 100 - (100 / (1 + (df["Close"].diff().clip(lower=0).ewm(com=13).mean() / -df["Close"].diff().clip(upper=0).ewm(com=13).mean())))
        df["AVG_VOL"] = df["Volume"].rolling(20).mean()
        return df
    except: return pd.DataFrame()

def process_stock(symbol):
    df = get_data(symbol)
    if df.empty or len(df) < 50: return None
    
    # Simple AI/Logic
    close = float(df['Close'].iloc[-1])
    trend = "BULLISH 🚀" if df['EMA20'].iloc[-1] > df['EMA50'].iloc[-1] else "BEARISH 🔻"
    rvol = df['Volume'].iloc[-1] / df['AVG_VOL'].iloc[-1]
    
    return [symbol, round(close, 2), trend, f"{rvol:.2f}x"]

# RUN
if run_scanner:
    stock_list = [s.strip() for s in symbols.split(",")]
    results = []
    
    with st.spinner("Scanning markets..."):
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(process_stock, s) for s in stock_list]
            for f in as_completed(futures):
                if f.result(): results.append(f.result())
    
    if results:
        df_res = pd.DataFrame(results, columns=["Stock", "LTP", "Trend", "RVOL"])
        st.dataframe(df_res, use_container_width=True)
        
        # Excel
        buffer = io.BytesIO()
        df_res.to_excel(buffer, index=False)
        st.download_button("📥 Download Excel", buffer.getvalue(), "Scanner_Report.xlsx")
