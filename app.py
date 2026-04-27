import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from io import BytesIO
from streamlit_autorefresh import st_autorefresh
import plotly.graph_objects as go

# =============================
# CONFIG & REFRESH
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V17", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V17 - ADVANCED TRADING SYSTEM")
st.write(f"🕒 Last Update: {now.strftime('%Y-%m-%d %H:%M:%S')}")

# =============================
# STOCK LIST
# =============================
stocks = [
    "RELIANCE","TCS","HDFCBANK","ICICIBANK","INFY","BHARTIARTL","SBIN","ITC","LT","BAJFINANCE",
    "AXISBANK","KOTAKBANK","HCLTECH","MARUTI","SUNPHARMA","TITAN","TATAMOTORS","ULTRACEMCO","ADANIENT","JSWSTEEL"
] 

# =============================
# CORE FUNCTIONS
# =============================
@st.cache_data(ttl=300)
def get_batch_data(stock_list, interval="5m", period="5d"):
    try:
        tickers = [s + ".NS" for s in stock_list]
        data = yf.download(tickers, period=period, interval=interval, group_by='ticker', progress=False)
        return data
    except: return None

def add_indicators(df):
    df = df.copy()
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-9)
    df['ATR'] = (df['High'] - df['Low']).rolling(14).mean()
    
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))
    
    return df

def get_smart_money(df):
    last = df.iloc[-1]
    avg_vol = df['Volume'].rolling(20).mean().iloc[-1]
    if last['Volume'] > avg_vol * 2:
        return "🔥 BIG PLAYER"
    return "Normal"

def ai_score(df):
    if len(df) < 2: return 0
    last = df.iloc[-1]
    score = 0
    if last['EMA20'] > last['EMA50']: score += 30
    if last['Close'] > last['VWAP']: score += 30
    if 45 < last['RSI'] < 75: score += 20
    if last['Volume'] > df['Volume'].rolling(20).mean().iloc[-1]: score += 20
    return score

# =============================
# TABS SETUP
# =============================
tab1, tab2, tab3, tab4 = st.tabs(["🔍 LIVE SCAN", "🎯 PULLBACK LIVE", "📊 GENERIC BACKTEST", "🔥 PB BACKTEST"])

all_data = get_batch_data(stocks)

# -----------------------------
# TAB 1: LIVE SCAN (Added Entry, SL, Target)
# -----------------------------
with tab1:
    if st.button("🚀 RUN LIVE SCAN"):
        res = []
        for s in stocks:
            try:
                df = all_data[s + ".NS"].dropna()
                df = add_indicators(df)
                sc = ai_score(df)
                last_p = round(df['Close'].iloc[-1], 2)
                atr = df['ATR'].iloc[-1]
                
                if sc >= 75 or sc <= 25:
                    side = "BUY" if sc >= 75 else "SELL"
                    res.append({
                        "TIME": df.index[-1].strftime('%H:%M'),
                        "STOCK": s,
                        "SIDE": side,
                        "ENTRY": last_p,
                        "SL": round(last_p - (atr * 1.5) if side == "BUY" else last_p + (atr * 1.5), 2),
                        "TARGET": round(last_p + (atr * 3) if side == "BUY" else last_p - (atr * 3), 2),
                        "SMART": get_smart_money(df),
                        "SCORE": sc
                    })
            except: continue
        st.table(pd.DataFrame(res)) if res else st.warning("No signals.")

# -----------------------------
# TAB 2: PULLBACK LIVE
# -----------------------------
with tab2:
    if st.button("🎯 SCAN PULLBACKS"):
        pb_res = []
        for s in stocks:
            try:
                df = all_data[s + ".NS"].dropna()
                df = add_indicators(df)
                last = df.iloc[-1]
                dist = abs(last['Close'] - last['EMA20']) / last['EMA20']
                
                if dist < 0.006: # Pullback range
                    side = ""
                    if last['EMA20'] > last['EMA50'] and last['Close'] > last['Open']: side = "BUY PB"
                    elif last['EMA20'] < last['EMA50'] and last['Close'] < last['Open']: side = "SELL PB"
                    
                    if side:
                        last_p = round(last['Close'], 2)
                        atr = last['ATR']
                        pb_res.append({
                            "TIME": df.index[-1].strftime('%H:%M'),
                            "STOCK": s,
                            "TYPE": side,
                            "ENTRY": last_p,
                            "SL": round(last_p - (atr * 1.2) if "BUY" in side else last_p + (atr * 1.2), 2),
                            "TARGET": round(last_p + (atr * 2.5) if "BUY" in side else last_p - (atr * 2.5), 2),
                            "SMART": get_smart_money(df)
                        })
            except: continue
        st.table(pd.DataFrame(pb_res)) if pb_res else st.warning("No Pullbacks.")

# -----------------------------
# TAB 3: GENERIC BACKTEST (Fixed Logic)
# -----------------------------
with tab3:
    test_date = st.date_input("Select Date", value=now.date() - timedelta(days=1), key="gen")
    if st.button("📊 RUN ACCURACY TEST"):
        gen_logs = []
        for s in stocks:
            try:
                df = all_data[s + ".NS"].dropna()
                df = add_indicators(df)
                df_day = df[df.index.date == test_date]
                for i in range(10, len(df_day)-5):
                    snap = df_day.iloc[:i+1]
                    sc = ai_score(snap)
                    if sc >= 80: # Strong Buy signal
                        entry = snap['Close'].iloc[-1]
                        future_max = df_day['High'].iloc[i+1:i+6].max() # Look ahead 5 candles
                        res = "WIN ✅" if future_max > entry else "LOSS ❌"
                        gen_logs.append({"STOCK": s, "TIME": df_day.index[i].strftime('%H:%M'), "SCORE": sc, "RESULT": res})
            except: continue
        if gen_logs:
            pdf = pd.DataFrame(gen_logs)
            win_rate = (pdf['RESULT'] == "WIN ✅").mean() * 100
            st.metric("Overall Accuracy", f"{win_rate:.2f}%")
            st.dataframe(pdf)

# -----------------------------
# TAB 4: PB BACKTEST (Corrected Time & Logic)
# -----------------------------
with tab4:
    pb_test_date = st.date_input("Select Date", value=now.date() - timedelta(days=1), key="pb_back")
    if st.button("🔥 RUN PB BACKTEST"):
        pb_logs = []
        for s in stocks:
            try:
                df = all_data[s + ".NS"].dropna()
                df = add_indicators(df)
                df_day = df[df.index.date == pb_test_date]
                for i in range(15, len(df_day)-2):
                    snap = df_day.iloc[:i+1]
                    last = snap.iloc[-1]
                    dist = abs(last['Close'] - last['EMA20']) / last['EMA20']
                    
                    if dist < 0.006:
                        entry = last['Close']
                        exit_p = df_day['Close'].iloc[i+2] # Check after 2 candles
                        
                        side = ""
                        if last['EMA20'] > last['EMA50'] and last['Close'] > last['Open']: 
                            side = "BUY PB"
                            res = "WIN ✅" if exit_p > entry else "LOSS ❌"
                        elif last['EMA20'] < last['EMA50'] and last['Close'] < last['Open']: 
                            side = "SELL PB"
                            res = "WIN ✅" if exit_p < entry else "LOSS ❌"
                        
                        if side:
                            pb_logs.append({"TIME": df_day.index[i].strftime('%H:%M'), "STOCK": s, "SIDE": side, "RESULT": res})
            except: continue
        st.dataframe(pd.DataFrame(pb_logs)) if pb_logs else st.warning("No trades found.")
