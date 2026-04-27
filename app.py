import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
import pytz

# =============================
# CONFIG & REFRESH
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V17 - BUY+SELL", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone('Asia/Kolkata')
current_time = datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')

st.title("🚀 NSE AI PRO V17 - ULTIMATE DASHBOARD")
st.write(f"🕒 **System Sync (IST):** {current_time}")

# =============================
# STOCK SECTORS
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
# UI - LIVE SCANNER
# =============================
if st.button("🚀 SCAN ALL NSE STOCKS"):
    live_results = []
    with st.spinner("Analyzing Live Entry Points..."):
        for s in all_stocks:
            df_l = yf.Ticker(s + ".NS").history(period="2d", interval="15m")
            if not df_l.empty:
                df_l.index = df_l.index.tz_convert(IST)
                df_l = add_indicators(df_l)
                last = df_l.iloc[-1]
                
                price = round(last['Close'], 2)
                sig = "WAIT"
                sl, tgt = 0, 0
                
                # ✅ BUY + SELL Logic
                if last['Close'] > last['VWAP'] and last['EMA20'] > last['EMA50']:
                    sig = "🚀 STRONG BUY"
                    sl = round(price * 0.99, 2)
                    tgt = round(price * 1.02, 2)
                
                elif last['Close'] < last['VWAP'] and last['EMA20'] < last['EMA50']:
                    sig = "🔻 STRONG SELL"
                    sl = round(price * 1.01, 2)
                    tgt = round(price * 0.98, 2)
                
                live_results.append({
                    "STOCK": s, "DATE": df_l.index[-1].strftime('%Y-%m-%d'),
                    "TIME": df_l.index[-1].strftime('%H:%M'),
                    "ENTRY": price, "SIGNAL": sig, "STOPLOSS": sl, "TARGET": tgt,
                    "ALERT": "🐋 BIG FISH" if last['Big_Player'] else "Normal"
                })
    if live_results:
        st.dataframe(pd.DataFrame(live_results), use_container_width=True)
