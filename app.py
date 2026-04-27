import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG & UI SETUP
# =============================
st.set_page_config(page_title="🚀 NSE AI PRO V23", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V23 - ADVANCED MULTI-FILTER SYSTEM")
st.write(f"🕒 **Market Time:** {now.strftime('%Y-%m-%d %H:%M:%S')} | **Status:** Active 🟢")

# =============================
# STOCK LIST
# =============================
stocks = [
    "RELIANCE","TCS","HDFCBANK","ICICIBANK","INFY","BHARTIARTL",
    "SBIN","ITC","LT","BAJFINANCE","AXISBANK","KOTAKBANK",
    "HCLTECH","MARUTI","SUNPHARMA","TITAN","TATAMOTORS",
    "ULTRACEMCO","ADANIENT","JSWSTEEL","M&M","NTPC","POWERGRID"
]

# =============================
# CORE INDICATORS (ENHANCED)
# =============================
def add_indicators(df):
    df = df.copy()
    if len(df) < 20: return df
    
    # EMAs
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    
    # VWAP
    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-9)
    
    # RSI (New)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # TRUE ATR
    high_low = df['High'] - df['Low']
    high_close = abs(df['High'] - df['Close'].shift())
    low_close = abs(df['Low'] - df['Close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()
    
    return df

# =============================
# DATA FETCHING
# =============================
@st.cache_data(ttl=60)
def fetch_data(symbols, interval, period):
    tickers = [s + ".NS" for s in symbols]
    try:
        data = yf.download(tickers, period=period, interval=interval, group_by='ticker', progress=False)
        return data
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

# Load All Data
data_5m = fetch_data(stocks, "5m", "5d")
data_15m = fetch_data(stocks, "15m", "5d") # Multi-Timeframe support
data_1d = fetch_data(stocks, "1d", "6mo")

# =============================
# SIDEBAR CONTROLS
# =============================
st.sidebar.header("⚙️ Trading Settings")
rsi_limit = st.sidebar.slider("Minimum RSI Filter", 40, 70, 55)
rr_ratio = st.sidebar.slider("Risk-Reward Ratio (Target)", 1.5, 5.0, 3.0)

# =============================
# TABS SETUP
# =============================
tab1, tab2, tab3, tab4 = st.tabs([
    "🔍 POWER SCANNER (1D+5M)", 
    "🎯 PULLBACK DETECTOR", 
    "📊 LIVE WATCHLIST",
    "🔥 PERFORMANCE BACKTEST"
])

# -----------------------------
# TAB 1: POWER SCANNER
# -----------------------------
with tab1:
    if st.button("🚀 EXECUTE FULL SCAN", key="pwr_scan"):
        res = []
        for s in stocks:
            try:
                df1 = add_indicators(data_1d[s + ".NS"].dropna())
                df5 = add_indicators(data_5m[s + ".NS"].dropna())
                
                last_1d = df1.iloc[-1]
                last_5m = df5.iloc[-1]
                
                # Trend Logic: 1D Bullish + 5M Above VWAP + RSI Check
                trend_1d = last_1d['Close'] > last_1d['EMA20']
                momentum_5m = last_5m['Close'] > last_5m['VWAP']
                rsi_check = last_5m['RSI'] > rsi_limit
                
                if trend_1d and momentum_5m and rsi_check:
                    entry = round(last_5m['Close'], 2)
                    atr = last_5m['ATR']
                    res.append({
                        "STOCK": s,
                        "SIGNAL": "STRONG BUY 🔥",
                        "ENTRY": entry,
                        "SL": round(entry - (atr * 1.5), 2),
                        "TARGET": round(entry + (atr * rr_ratio), 2),
                        "RSI": round(last_5m['RSI'], 1),
                        "VOL": "HIGH" if last_5m['Volume'] > df5['Volume'].rolling(20).mean().iloc[-1]*2 else "NORMAL"
                    })
            except: continue
        
        if res: st.table(pd.DataFrame(res))
        else: st.info("No strong trend stocks found with current filters.")

# -----------------------------
# TAB 2: PULLBACK DETECTOR
# -----------------------------
with tab2:
    if st.button("🎯 FIND PULLBACKS"):
        pb_res = []
        for s in stocks:
            try:
                df5 = add_indicators(data_5m[s + ".NS"].dropna())
                last = df5.iloc[-1]
                
                dist = abs(last['Close'] - last['EMA20']) / last['EMA20']
                
                # Pullback Condition: Near EMA20 + Green Candle
                if dist < 0.004 and last['Close'] > last['Open']:
                    pb_res.append({
                        "STOCK": s,
                        "PRICE": round(last['Close'], 2),
                        "PB ZONE": "EMA20 ✅",
                        "ATR SL": round(last['Close'] - last['ATR'], 2),
                        "RSI": round(last['RSI'], 1)
                    })
            except: continue
        
        if pb_res: st.dataframe(pd.DataFrame(pb_res), use_container_width=True)
        else: st.warning("No pullbacks detected near EMA20.")

# -----------------------------
# TAB 4: BACKTEST (IMPROVED)
# -----------------------------
with tab4:
    col1, col2 = st.columns(2)
    with col1:
        bt_date = st.date_input("Analysis Date", value=now.date() - timedelta(days=1))
    
    if st.button("🔥 RUN ACCURATE BACKTEST"):
        logs = []
        for s in stocks:
            try:
                df = add_indicators(data_5m[s + ".NS"].dropna())
                df_day = df[df.index.date == bt_date]
                if df_day.empty: continue
                
                for i in range(20, len(df_day)-10):
                    snap = df_day.iloc[:i+1]
                    last = snap.iloc[-1]
                    
                    # Backtest Pullback logic
                    if (abs(last['Close'] - last['EMA20']) / last['EMA20']) < 0.005:
                        entry = last['Close']
                        atr = last['ATR']
                        future = df_day.iloc[i+1 : i+11] # Look 10 candles ahead
                        
                        target_p = entry + (atr * 2)
                        sl_p = entry - atr
                        
                        win = any(future['High'] >= target_p)
                        loss = any(future['Low'] <= sl_p)
                        
                        if win: status = "PROFIT ✅"
                        elif loss: status = "STOPLOSS ❌"
                        else: status = "EXPIRED ⚪"
                        
                        logs.append({"STOCK": s, "TIME": df_day.index[i].strftime('%H:%M'), "RESULT": status})
                        break # Only one test per stock per day to avoid clutter
            except: continue
        
        if logs: st.table(pd.DataFrame(logs))
        else: st.info("No signals to test for the selected date.")
