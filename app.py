import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import io
import requests
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from xgboost import XGBClassifier

warnings.filterwarnings("ignore")

# PAGE CONFIG
st.set_page_config(page_title="NSE AI PRO V11.14", layout="wide", page_icon="🚀")
st.title("🚀 NSE AI PRO V11.14 - Institutional Edition")

# SIDEBAR
with st.sidebar:
    interval = st.selectbox("Interval", ["5m", "15m", "30m", "1h", "1d"], index=1)
    period = st.selectbox("Period", ["5d", "1mo", "3mo", "6mo", "1y"], index=2)
    run_scanner = st.button("🚀 RUN SCANNER")

# FUNCTIONS
def get_data(symbol, interval, period):
    try:
        df = yf.download(f"{symbol}.NS", interval=interval, period=period, progress=False, threads=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        return df
    except: return pd.DataFrame()

def process_stock(symbol, interval, period):
    df = get_data(symbol, interval, period)
    if df.empty or len(df) < 50: return None
    
    # Indicators
    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()
    df["RSI"] = 100 - (100 / (1 + (df["Close"].diff().clip(lower=0).ewm(com=13).mean() / -df["Close"].diff().clip(upper=0).ewm(com=13).mean())))
    df["AVG_VOL"] = df["Volume"].rolling(20).mean()
    
    # AI Trend
    try:
        df_ml = df.dropna().copy()
        df_ml['Target'] = np.where(df_ml['Close'].shift(-1) > df_ml['Close'], 1, 0)
        df_ml.dropna(inplace=True)
        X = df_ml[['EMA20', 'EMA50', 'RSI']].values.astype('float32')
        y = df_ml['Target'].values.astype('int32')
        model = XGBClassifier(n_estimators=10, max_depth=3, n_jobs=1)
        model.fit(X[:-1], y[:-1])
        pred = int(model.predict(X[-1].reshape(1, -1))[0])
        trend = "BULLISH 🚀" if pred == 1 else "BEARISH 🔻"
    except: trend = "NEUTRAL"
    
    # Momentum
    prev_close = df['Close'].iloc[-2]
    gap = ((df['Open'].iloc[-1] - prev_close)/prev_close)*100
    rvol = df['Volume'].iloc[-1] / df['AVG_VOL'].iloc[-1]
    
    return [symbol, round(float(df['Close'].iloc[-1]), 2), f"{gap:.2f}%", trend, f"{rvol:.2f}x"]

# EXECUTION
if run_scanner:
    symbols = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "SBIN", "TATAMOTORS", "ITC"]
    results = []
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(process_stock, s, interval, period) for s in symbols]
        for f in as_completed(futures):
            res = f.result()
            if res: results.append(res)
            
    if results:
        df_res = pd.DataFrame(results, columns=["Stock", "LTP", "Gap", "AI Trend", "RVOL"])
        st.dataframe(df_res, use_container_width=True)
        
        # DOWNLOAD
        excel_buffer = io.BytesIO()
        df_res.to_excel(excel_buffer, index=False)
        st.download_button("📥 Download Excel", excel_buffer.getvalue(), "Report.xlsx")
