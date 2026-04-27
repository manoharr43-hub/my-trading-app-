import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🚀 NSE AI PRO V18", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V18 - PRO FIX")
st.write(f"🕒 Market Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")

# =============================
# STOCK LIST
# =============================
stocks = ["RELIANCE","TCS","HDFCBANK","ICICIBANK","INFY","BHARTIARTL","SBIN","ITC","LT","BAJFINANCE",
          "AXISBANK","KOTAKBANK","HCLTECH","MARUTI","SUNPHARMA","TITAN","TATAMOTORS","ULTRACEMCO","ADANIENT","JSWSTEEL"]

# =============================
# INDICATORS & SMART MONEY
# =============================
def add_indicators(df):
    df = df.copy()
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-9)
    df['ATR'] = (df['High'] - df['Low']).rolling(14).mean()
    return df

def get_smart_money(df):
    last = df.iloc[-1]
    avg_vol = df['Volume'].rolling(20).mean().iloc[-1]
    return "🔥 BIG PLAYER" if last['Volume'] > avg_vol * 1.8 else "Normal"

# =============================
# TABS
# =============================
tab1, tab2, tab3, tab4 = st.tabs(["🔍 LIVE SCAN", "🎯 PULLBACK LIVE", "📊 GENERIC BACKTEST", "🔥 PB BACKTEST"])

# Batch Data Fetch
@st.cache_data(ttl=60)
def fetch_data():
    tickers = [s + ".NS" for s in stocks]
    return yf.download(tickers, period="5d", interval="5m", group_by='ticker', progress=False)

all_data = fetch_data()

# -----------------------------
# TAB 1: LIVE SCAN
# -----------------------------
with tab1:
    if st.button("🚀 START SCAN"):
        res = []
        for s in stocks:
            try:
                df = all_data[s + ".NS"].dropna()
                df = add_indicators(df)
                last_p = round(df['Close'].iloc[-1], 2)
                atr = df['ATR'].iloc[-1]
                
                # Simple Logic for Trend
                if last_p > df['EMA20'].iloc[-1] and last_p > df['VWAP'].iloc[-1]:
                    side = "BUY"
                    res.append({
                        "TIME": df.index[-1].strftime('%H:%M'), "STOCK": s, "SIDE": side,
                        "ENTRY": last_p, "SL": round(last_p - (atr*1.5), 2),
                        "TARGET": round(last_p + (atr*3), 2), "SMART": get_smart_money(df)
                    })
            except: continue
        if res: st.dataframe(pd.DataFrame(res), use_container_width=True)
        else: st.info("No Trend Signals.")

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
                
                if dist < 0.005: # Price near EMA20
                    side = "BUY PB" if last['Close'] > last['Open'] and last['EMA20'] > last['EMA50'] else "SELL PB" if last['Close'] < last['Open'] and last['EMA20'] < last['EMA50'] else ""
                    if side:
                        pb_res.append({
                            "TIME": df.index[-1].strftime('%H:%M'), "STOCK": s, "TYPE": side,
                            "ENTRY": round(last['Close'],2), "SL": round(last['Close'] - last['ATR'] if "BUY" in side else last['Close'] + last['ATR'], 2),
                            "TARGET": round(last['Close'] + (last['ATR']*2) if "BUY" in side else last['Close'] - (last['ATR']*2), 2),
                            "SMART": get_smart_money(df)
                        })
            except: continue
        if pb_res: st.dataframe(pd.DataFrame(pb_res), use_container_width=True)
        else: st.info("Waiting for Pullback setups...")

# -----------------------------
# TAB 4: PB BACKTEST (FIXED)
# -----------------------------
with tab4:
    date_in = st.date_input("Test Date", value=now.date() - timedelta(days=1))
    if st.button("🔥 RUN BACKTEST"):
        pb_logs = []
        for s in stocks:
            try:
                df = all_data[s + ".NS"].dropna()
                df = add_indicators(df)
                df_day = df[df.index.date == date_in]
                for i in range(10, len(df_day)-3):
                    snap = df_day.iloc[:i+1]
                    dist = abs(snap['Close'].iloc[-1] - snap['EMA20'].iloc[-1]) / snap['EMA20'].iloc[-1]
                    if dist < 0.005:
                        entry = snap['Close'].iloc[-1]
                        future_close = df_day['Close'].iloc[i+2]
                        side = "BUY" if snap['EMA20'].iloc[-1] > snap['EMA50'].iloc[-1] else "SELL"
                        res = "WIN ✅" if (side == "BUY" and future_close > entry) or (side == "SELL" and future_close < entry) else "LOSS ❌"
                        pb_logs.append({"TIME": df_day.index[i].strftime('%H:%M'), "STOCK": s, "SIDE": side, "RESULT": res})
            except: continue
        if pb_logs: st.dataframe(pd.DataFrame(pb_logs), use_container_width=True)
