import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings

warnings.filterwarnings('ignore')

st.set_page_config(page_title="NSE AI PRO V11.10", layout="wide")

# 1. NSE 500 LIST
@st.cache_data(ttl=86400)
def load_nse500():
    try:
        import requests
        url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        df = pd.read_csv(io.StringIO(response.text))
        return df["Symbol"].dropna().unique().tolist()
    except:
        return ["RELIANCE", "TCS", "INFY", "HDFCBANK", "SBIN"]

# 2. CALCULATE INDICATORS
def add_indicators(df):
    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()
    df["VWAP"] = (df["Volume"] * (df["High"] + df["Low"] + df["Close"]) / 3).cumsum() / df["Volume"].cumsum()
    df["AVG_VOL"] = df["Volume"].rolling(20).mean()
    return df

# 3. PROCESS SINGLE STOCK
def process_stock(symbol):
    df = yf.download(f"{symbol}.NS", period="5d", interval="15m", progress=False, auto_adjust=True)
    if df.empty or len(df) < 20: return None
    df = add_indicators(df)
    
    curr = df.iloc[-1]
    prev = df.iloc[-2]
    
    # Logic
    gap_pct = ((curr['Open'] - prev['Close']) / prev['Close']) * 100
    atr = (curr['High'] - curr['Low']) # Simple ATR
    target = curr['Close'] + (atr * 2)
    stoploss = curr['Close'] - (atr * 1)
    
    return {
        "Stock": symbol,
        "LTP": round(curr['Close'], 2),
        "Gap %": f"{round(gap_pct, 2)}%",
        "Target": round(target, 2),
        "Stoploss": round(stoploss, 2),
        "VWAP": round(curr['VWAP'], 2),
        "RVOL": round(curr['Volume'] / curr['AVG_VOL'], 2),
        "Alerts": "📰 NEWS" if abs(gap_pct) > 2 else "Normal"
    }

# 4. UI
st.title("🚀 NSE AI PRO V11.10 - Institutional Ultimate")
if st.button("🚀 RUN FULL 500 SCANNER"):
    stocks = load_nse500()
    results = []
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = {executor.submit(process_stock, s): s for s in stocks}
        for future in as_completed(futures):
            res = future.result()
            if res: results.append(res)
    
    st.session_state.data = pd.DataFrame(results)

if 'data' in st.session_state:
    st.dataframe(st.session_state.data, use_container_width=True)
    csv = st.session_state.data.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Master Report", csv, "NSE_AI_PRO_Report.csv", "text/csv")
