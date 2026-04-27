import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
import pytz
import time

# =============================
# CONFIG & REFRESH
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V21 - LIVE+BACKTEST", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone('Asia/Kolkata')
current_time = datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')

st.title("🚀 NSE AI PRO V21 - ULTIMATE DASHBOARD")
st.write(f"🕒 **System Sync (IST):** {current_time}")

# =============================
# STOCK SECTORS + ALL OPTIONS
# =============================
sector_map = {
    "BANKING": ["HDFCBANK", "ICICIBANK", "SBIN", "AXISBANK", "KOTAKBANK"],
    "IT": ["TCS", "INFY", "HCLTECH", "WIPRO", "TECHM"],
    "AUTO": ["TATAMOTORS", "M&M", "MARUTI", "BAJAJ-AUTO", "EICHERMOT"],
    "ENERGY": ["RELIANCE", "NTPC", "POWERGRID", "ONGC", "BPCL"],
    "OTHERS": ["ITC", "LT", "BAJFINANCE", "TATASTEEL", "BHARTIARTL"]
}
all_stocks = [s for sub in sector_map.values() for s in sub]

# =============================
# SAFE LOADER (Rate Limit Fix)
# =============================
def safe_history(ticker, period="2d", interval="15m", retries=3, delay=5):
    for i in range(retries):
        try:
            df = yf.Ticker(ticker + ".NS").history(period=period, interval=interval)
            if not df.empty:
                return df
        except Exception as e:
            time.sleep(delay)
    return pd.DataFrame()

# =============================
# CORE FUNCTIONS
# =============================
def get_clean_data(stock, period="1y", interval="1d"):
    try:
        df = yf.Ticker(stock + ".NS").history(period=period, interval=interval)
        if df.empty: return None
        df.index = df.index.tz_localize(None)
        return df.dropna()
    except: return None

def add_indicators(df):
    df = df.copy()
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    
    # ✅ RSI Fix
    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/14, min_periods=14).mean()
    avg_loss = loss.ewm(alpha=1/14, min_periods=14).mean()
    rs = avg_gain / (avg_loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # ✅ VWAP Daily Reset
    df['CumVol'] = df['Volume'].groupby(df.index.date).cumsum()
    df['CumPV'] = (df['Close'] * df['Volume']).groupby(df.index.date).cumsum()
    df['VWAP'] = df['CumPV'] / df['CumVol']
    
    df['Vol_Avg'] = df['Volume'].rolling(20).mean()
    df['Big_Player'] = df['Volume'] > (df['Vol_Avg'] * 2.5)
    df['Bull_Rev'] = (df['RSI'].shift(1) < 30) & (df['RSI'] > 30)
    return df

# =============================
# UI - TABS
# =============================
tab1, tab2, tab3 = st.tabs(["🔍 LIVE SCANNER (ALL)", "📊 30-DAY BACKTEST REPORT", "📈 CHART ANALYSIS"])

with tab1:
    if st.button("🚀 SCAN ALL NSE STOCKS"):
        live_results = []
        with st.spinner("Analyzing Live Entry Points..."):
            for s in all_stocks:
                df_l = safe_history(s, period="2d", interval="15m")
                if not df_l.empty:
                    df_l.index = df_l.index.tz_convert(IST)
                    df_l = add_indicators(df_l)
                    last = df_l.iloc[-1]
                    
                    price = round(last['Close'], 2)
                    sig = "WAIT"
