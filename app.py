import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from streamlit_autorefresh import st_autorefresh
import io

# =============================
# CONFIG & UI SETUP
# =============================
st.set_page_config(page_title="🚀 NSE AI PRO V31", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V31 - PULLBACK & BACKTEST MASTER")
st.write(f"🕒 **Market Time:** {now.strftime('%Y-%m-%d %H:%M:%S')}")

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
# CORE INDICATORS (V31)
# =============================
def add_indicators(df, interval='5m'):
    df = df.copy()
    if len(df) < 20: return df
    
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-9)
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))
    
    high_low = df['High'] - df['Low']
    tr = pd.concat([high_low, abs(df['High'] - df['Close'].shift()), abs(df['Low'] - df['Close'].shift())], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()
    df['VolAvg'] = df['Volume'].rolling(20).mean()
    
    if interval == '1d':
        df['PP'] = (df['High'] + df['Low'] + df['Close']) / 3
        df['S1'] = (2 * df['PP']) - df['High']
        df['R1'] = (2 * df['PP']) - df['Low']
        
    return df

@st.cache_data(ttl=60)
def fetch_data(symbols, interval, period):
    tickers = [s + ".NS" for s in symbols]
    return yf.download(tickers, period=period, interval=interval, group_by='ticker', progress=False)

data_5m = fetch_data(stocks, "5m", "5d")
data_1d = fetch_data(stocks, "1d", "6mo")

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Trading_Data')
    return output.getvalue()

# =============================
# TABS
# =============================
tab1, tab2, tab3 = st.tabs(["🔥 LIVE PULLBACK SCANNER", "🔍 ALL SIGNALS WATCH", "📊 FIXED BACKTEST"])

# -----------------------------
# TAB 1: LIVE PULLBACK SCANNER (Support/Resistance)
# -----------------------------
with tab1:
    if st.button("SCAN PULLBACKS NOW"):
        pb_res = []
        for s in stocks:
            try:
                df1 = add_indicators(data_1d[s + ".NS"].dropna(), '1d')
                df5 = add_indicators(data_5m[s + ".NS"].dropna(), '5m')
                l1, l5 = df1.iloc[-2], df5.iloc[-1] # Prev Day Pivot, Current 5m
                
                curr_p = l5['Close']
                ema = l5['EMA20']
                s1, r1 = l1['S1'], l1['R1']
                atr = l5['ATR']
                
                # --- BUY @ SUPPORT ---
                if (abs(curr_p - s1)/s1 < 0.003 or abs(curr_p - ema)/ema < 0.003) and curr_p > l5['Open']:
                    pb_res.append({
                        "TIME": df5.index[-1].astimezone(IST).strftime('%H:%M'),
                        "STOCK": s, "ACTION": "BUY 🟢 (Support PB)", "ENTRY": round(curr_p, 2),
                        "BIG PLAYER": "🔥" if l5['Volume'] > l5['VolAvg']*2 else "-",
                        "SL": round(curr_p - atr, 2), "TARGET": round(curr_p + (atr*2.5), 2)
                    })
                
                # --- SELL @ RESISTANCE ---
                elif (abs(curr_p - r1)/r1 < 0.003 or abs(curr_p - ema)/ema < 0.003) and curr_p < l5['Open']:
                    pb_res.append({
                        "TIME": df5.index[-1].astimezone(IST).strftime('%H:%M'),
                        "STOCK": s, "ACTION": "SELL 🔴 (Resist PB)", "ENTRY": round(curr_p, 2),
                        "BIG PLAYER": "🔥" if l5['Volume'] > l5['VolAvg']*2 else "-",
                        "SL": round(curr_p + atr, 2), "TARGET": round(curr_p - (atr*2.5), 2)
                    })
            except: continue
        if pb_res: st.table(pd.DataFrame(pb_res))
        else: st.info("No Pullback entries found in current candle.")

# -----------------------------
# TAB 3: BACKTEST (WORKING FIX)
# -----------------------------
with tab3:
    bt_date = st.date_input("Select History Date", value=now.date() - timedelta(days=1))
    if st.button("RUN FULL BACKTEST"):
        bt_logs = []
        for s in stocks:
            try:
                df = data_5m[s + ".NS"].dropna()
                df.index = df.index.tz_convert(IST)
                df_day = add_indicators(df[df.index.date == bt_date])
                
                if df_day is None or df_day.empty: continue

                for i in range(15, len(df_day)):
                    row
