import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG & REFRESH
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V20", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V20 - 1H TREND + SMART ENTRY")
st.write(f"🕒 Current Market Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")

# =============================
# STOCK LIST
# =============================
stocks = ["RELIANCE","TCS","HDFCBANK","ICICIBANK","INFY","BHARTIARTL","SBIN","ITC","LT","BAJFINANCE",
          "AXISBANK","KOTAKBANK","HCLTECH","MARUTI","SUNPHARMA","TITAN","TATAMOTORS","ULTRACEMCO","ADANIENT","JSWSTEEL"]

# =============================
# CORE FUNCTIONS
# =============================
def add_indicators(df):
    df = df.copy()
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-9)
    df['ATR'] = (df['High'] - df['Low']).rolling(14).mean()
    # RSI for scoring
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

@st.cache_data(ttl=60)
def fetch_batch(stock_list, interval, period):
    tickers = [s + ".NS" for s in stock_list]
    return yf.download(tickers, period=period, interval=interval, group_by='ticker', progress=False)

# =============================
# TABS SETUP
# =============================
tab1, tab2, tab3, tab4 = st.tabs(["🔍 LIVE SCAN (1H)", "🎯 PULLBACK LIVE (1H)", "📊 GENERIC BACKTEST", "🔥 PB BACKTEST"])

# Pre-fetch data for all tabs
data_5m = fetch_batch(stocks, "5m", "5d")
data_1h = fetch_batch(stocks, "1h", "1mo")

# -----------------------------
# TAB 1: LIVE SCAN (1H TREND ALIGNED)
# -----------------------------
with tab1:
    if st.button("🚀 RUN 1H ALIGNED SCAN", key="btn_scan"):
        results = []
        for s in stocks:
            try:
                # 1H Trend Analysis
                df_1h = add_indicators(data_1h[s + ".NS"].dropna())
                df_5m = add_indicators(data_5m[s + ".NS"].dropna())
                
                trend_1h = "UP" if df_1h['Close'].iloc[-1] > df_1h['EMA20'].iloc[-1] else "DOWN"
                last_p = round(df_5m['Close'].iloc[-1], 2)
                atr = df_5m['ATR'].iloc[-1]
                
                # Entry only if 5m aligns with 1H trend
                if trend_1h == "UP" and last_p > df_5m['VWAP'].iloc[-1]:
                    results.append({
                        "TIME": df_5m.index[-1].strftime('%H:%M'),
                        "STOCK": s, "SIDE": "BUY 🟢", "1H": "BULLISH",
                        "ENTRY": last_p, "SL": round(last_p - (atr*1.5), 2),
                        "TARGET": round(last_p + (atr*3), 2),
                        "SMART": "🔥 BIG" if df_5m['Volume'].iloc[-1] > df_5m['Volume'].rolling(20).mean().iloc[-1]*2 else "Normal"
                    })
                elif trend_1h == "DOWN" and last_p < df_5m['VWAP'].iloc[-1]:
                    results.append({
                        "TIME": df_5m.index[-1].strftime('%H:%M'),
                        "STOCK": s, "SIDE": "SELL 🔴", "1H": "BEARISH",
                        "ENTRY": last_p, "SL": round(last_p + (atr*1.5), 2),
                        "TARGET": round(last_p - (atr*3), 2),
                        "SMART": "🔥 BIG" if df_5m['Volume'].iloc[-1] > df_5m['Volume'].rolling(20).mean().iloc[-1]*2 else "Normal"
                    })
            except: continue
        if results: st.dataframe(pd.DataFrame(results), use_container_width=True)
        else: st.info("No 1-Hour aligned trades found.")

# -----------------------------
# TAB 2: PULLBACK LIVE (1H SUPPORT)
# -----------------------------
with tab2:
    if st.button("🎯 SCAN 1H PULLBACKS", key="btn_pb"):
        pb_results = []
        for s in stocks:
            try:
                df_1h = add_indicators(data_1h[s + ".NS"].dropna())
                df_5m = add_indicators(data_5m[s + ".NS"].dropna())
                last_5m = df_5m.iloc[-1]
                
                dist = abs(last_5m['Close'] - last_5m['EMA20']) / last_5m['EMA20']
                
                if dist < 0.005: # Near EMA 20
                    side = ""
                    if df_1h['Close'].iloc[-1] > df_1h['EMA20'].iloc[-1] and last_5m['Close'] > last_5m['Open']:
                        side = "BUY PB"
                    elif df_1h['Close'].iloc[-1] < df_1h['EMA20'].iloc[-1] and last_5m['Close'] < last_5m['Open']:
                        side = "SELL PB"
                    
                    if side:
                        pb_results.append({
                            "TIME": df_5m.index[-1].strftime('%H:%M'), "STOCK": s, "TYPE": side,
                            "ENTRY": round(last_5m['Close'], 2),
                            "SL": round(last_5m['Close'] - last_5m['ATR'] if "BUY" in side else last_5m['Close'] + last_5m['ATR'], 2),
                            "TARGET": round(last_5m['Close'] + (last_5m['ATR']*2.5) if "BUY" in side else last_5m['Close'] - (last_5m['ATR']*2.5), 2)
                        })
            except: continue
        if pb_results: st.dataframe(pd.DataFrame(pb_results), use_container_width=True)
        else: st.info("Waiting for Pullback setups near 1H levels...")

# -----------------------------
# TAB 4: PB BACKTEST (TIME & LOGIC FIXED)
# -----------------------------
with tab4:
    test_date = st.date_input("Select Date", value=now.date() - timedelta(days=1), key="pb_date")
    if st.button("🔥 RUN ACCURATE BACKTEST", key="btn_bt"):
        logs = []
        for s in stocks:
            try:
                df = add_indicators(data_5m[s + ".NS"].dropna())
                df_day = df[df.index.date == test_date]
                for i in range(15, len(df_day)-5):
                    snap = df_day.iloc[:i+1]
                    last = snap.iloc[-1]
                    dist = abs(last['Close'] - last['EMA20']) / last['EMA20']
                    
                    if dist < 0.005:
                        entry_p = last['Close']
                        exit_p = df_day['Close'].iloc[i+3] # Check result after 3 candles
                        side = "BUY" if last['EMA20'] > last['EMA50'] else "SELL"
                        
                        res = "WIN ✅" if (side == "BUY" and exit_p > entry_p) or (side == "SELL" and exit_p < entry_p) else "LOSS ❌"
                        logs.append({
                            "ENTRY_TIME": df_day.index[i].strftime('%H:%M'),
                            "STOCK": s, "SIDE": side, "ENTRY": round(entry_p,2),
                            "EXIT_PRICE": round(exit_p,2), "RESULT": res
                        })
            except: continue
        if logs: st.dataframe(pd.DataFrame(logs), use_container_width=True)
        else: st.warning("No Pullback signals found for this date.")
