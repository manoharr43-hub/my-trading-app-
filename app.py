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
st.set_page_config(page_title="🚀 NSE AI PRO V27", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V27 - SUPPORT PULLBACK BUY/SELL")
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
# CORE INDICATORS
# =============================
def add_indicators(df, interval='5m'):
    df = df.copy()
    if len(df) < 20: return df
    
    # EMAs & VWAP
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-9)
    
    # RSI & ATR
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))
    
    high_low = df['High'] - df['Low']
    high_close = abs(df['High'] - df['Close'].shift())
    low_close = abs(df['Low'] - df['Close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()
    
    # Big Player Volume
    df['VolAvg'] = df['Volume'].rolling(20).mean()
    
    # Pivot Points (Daily)
    if interval == '1d':
        df['PP'] = (df['High'] + df['Low'] + df['Close']) / 3
        df['R1'] = (2 * df['PP']) - df['Low']
        df['S1'] = (2 * df['PP']) - df['High']
        
    return df

# =============================
# DATA FETCHING
# =============================
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
tab1, tab2, tab3 = st.tabs(["🔍 TREND SCANNER", "🎯 SUPPORT PULLBACK (BUY/SELL)", "📊 HISTORY BACKTEST"])

# -----------------------------
# 1. TREND SCANNER
# -----------------------------
with tab1:
    if st.button("START TREND SCAN"):
        res = []
        for s in stocks:
            try:
                df1 = add_indicators(data_1d[s + ".NS"].dropna(), '1d')
                df5 = add_indicators(data_5m[s + ".NS"].dropna(), '5m')
                l1, l5 = df1.iloc[-1], df5.iloc[-1]
                
                sig = "None"
                if l1['Close'] > l1['EMA20'] and l5['Close'] > l5['VWAP']: sig = "BUY 🟢"
                elif l1['Close'] < l1['EMA20'] and l5['Close'] < l5['VWAP']: sig = "SELL 🔴"
                
                if sig != "None":
                    res.append({
                        "TIME": df5.index[-1].astimezone(IST).strftime('%H:%M'),
                        "STOCK": s, "ACTION": sig,
                        "PRICE": round(l5['Close'], 2),
                        "BIG_PLAYER": "🔥 YES" if l5['Volume'] > (l5['VolAvg'] * 2) else "No",
                        "RSI": round(l5['RSI'], 1)
                    })
            except: continue
        if res:
            st.dataframe(pd.DataFrame(res), use_container_width=True)
        else: st.info("No strong trends right now.")

# -----------------------------
# 2. SUPPORT PULLBACK (BUY/SELL MENTIONED)
# -----------------------------
with tab2:
    if st.button("SCAN PULLBACK SIGNALS"):
        pb_res = []
        for s in stocks:
            try:
                df1 = add_indicators(data_1d[s + ".NS"].dropna(), '1d')
                df5 = add_indicators(data_5m[s + ".NS"].dropna(), '5m')
                l1, l5 = df1.iloc[-2], df5.iloc[-1] # Previous day pivots
                
                curr_p = l5['Close']
                ema20 = l5['EMA20']
                s1, r1 = l1['S1'], l1['R1']
                
                # Logic for BUY Pullback (Near Support)
                if abs(curr_p - s1)/s1 < 0.003 or abs(curr_p - ema20)/ema20 < 0.003:
                    if curr_p > l5['Open']: # Green Candle
                        pb_res.append({
                            "TIME": df5.index[-1].astimezone(IST).strftime('%H:%M'),
                            "STOCK": s, "ACTION": "BUY AT SUPPORT 🟢",
                            "PRICE": round(curr_p, 2), "ZONE": "S1/EMA20",
                            "SL": round(curr_p - l5['ATR'], 2),
                            "TARGET": round(curr_p + (l5['ATR']*2), 2)
                        })
                
                # Logic for SELL Pullback (Near Resistance)
                elif abs(curr_p - r1)/r1 < 0.003 or abs(curr_p - ema20)/ema20 < 0.003:
                    if curr_p < l5['Open']: # Red Candle
                        pb_res.append({
                            "TIME": df5.index[-1].astimezone(IST).strftime('%H:%M'),
                            "STOCK": s, "ACTION": "SELL AT RESISTANCE 🔴",
                            "PRICE": round(curr_p, 2), "ZONE": "R1/EMA20",
                            "SL": round(curr_p + l5['ATR'], 2),
                            "TARGET": round(curr_p - (l5['ATR']*2), 2)
                        })
            except: continue
        if pb_res:
            pb_df = pd.DataFrame(pb_res)
            st.table(pb_df)
            st.download_button("📥 Download Pullback Excel", data=to_excel(pb_df), file_name="Pullback_Signals.xlsx")
        else: st.warning("No Pullback entries found at the moment.")

# -----------------------------
# 3. BACKTEST
# -----------------------------
with tab3:
    bt_date = st.date_input("Backtest Date", value=now.date() - timedelta(days=1))
    if st.button("RUN BACKTEST"):
        logs = []
        for s in stocks:
            try:
                df = add_indicators(data_5m[s + ".NS"].dropna())
                df.index = df.index.tz_convert(IST)
                df_day = df[df.index.date == bt_date]
                if df_day.empty: continue

                for i in range(15, len(df_day)):
                    row = df_day.iloc[i]
                    is_pb = abs(row['Close'] - row['EMA20']) / row['EMA20'] < 0.004
                    if is_pb:
                        logs.append({
                            "TIME": df_day.index[i].strftime('%H:%M'),
                            "STOCK": s, "TYPE": "PULLBACK",
                            "PRICE": round(row['Close'], 2),
                            "RSI": round(row['RSI'], 1)
                        })
            except: continue
        if logs:
            st.dataframe(pd.DataFrame(logs), use_container_width=True)
        else: st.error("No data found.")
