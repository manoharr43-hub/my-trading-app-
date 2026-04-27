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
st.set_page_config(page_title="🚀 NSE AI PRO V28", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V28 - BUY/SELL PULLBACK MASTER")
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
# CORE INDICATORS (V28)
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
    
    # Big Player Analysis
    df['VolAvg'] = df['Volume'].rolling(20).mean()
    
    # Pivot Points (Resistance & Support)
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
        df.to_excel(writer, index=False, sheet_name='Pullback_Data')
    return output.getvalue()

# =============================
# TABS
# =============================
tab1, tab2, tab3 = st.tabs(["🚀 LIVE TRENDS", "🎯 PULLBACK (BUY/SELL)", "📊 HISTORY LOGS"])

# -----------------------------
# 1. LIVE TRENDS
# -----------------------------
with tab1:
    if st.button("RUN TREND SCAN"):
        res = []
        for s in stocks:
            try:
                df1 = add_indicators(data_1d[s + ".NS"].dropna(), '1d')
                df5 = add_indicators(data_5m[s + ".NS"].dropna(), '5m')
                l1, l5 = df1.iloc[-1], df5.iloc[-1]
                
                sig = "Neutral"
                if l5['Close'] > l5['VWAP'] and l5['RSI'] > 55: sig = "BULLISH 📈"
                elif l5['Close'] < l5['VWAP'] and l5['RSI'] < 45: sig = "BEARISH 📉"
                
                res.append({
                    "TIME": df5.index[-1].astimezone(IST).strftime('%H:%M'),
                    "STOCK": s, "TREND": sig, "PRICE": round(l5['Close'], 2),
                    "VOL_SPIKE": "🔥" if l5['Volume'] > l5['VolAvg']*2 else "-"
                })
            except: continue
        st.dataframe(pd.DataFrame(res), use_container_width=True)

# -----------------------------
# 2. PULLBACK BUY & SELL (MENTIONED CLEARLY)
# -----------------------------
with tab2:
    st.subheader("🎯 Buy at Support & Sell at Resistance")
    if st.button("SCAN FOR PULLBACK ENTRIES"):
        pb_list = []
        for s in stocks:
            try:
                df1 = add_indicators(data_1d[s + ".NS"].dropna(), '1d')
                df5 = add_indicators(data_5m[s + ".NS"].dropna(), '5m')
                l1, l5 = df1.iloc[-2], df5.iloc[-1] # Prev Day Pivot Data
                
                price = l5['Close']
                ema = l5['EMA20']
                s1, r1 = l1['S1'], l1['R1']
                atr = l5['ATR']
                
                # --- BUY PULLBACK (Support) ---
                dist_s1 = abs(price - s1) / s1
                dist_ema = abs(price - ema) / ema
                
                if (dist_s1 < 0.003 or dist_ema < 0.003) and price > l5['Open']:
                    pb_list.append({
                        "TIME": df5.index[-1].astimezone(IST).strftime('%H:%M'),
                        "STOCK": s, "ACTION": "BUY 🟢 (Support)",
                        "PRICE": round(price, 2), "LEVEL": "S1/EMA20",
                        "SL": round(price - atr, 2), "TARGET": round(price + (atr*2.5), 2)
                    })
                
                # --- SELL PULLBACK (Resistance) ---
                dist_r1 = abs(price - r1) / r1
                if (dist_r1 < 0.003 or dist_ema < 0.003) and price < l5['Open']:
                    pb_list.append({
                        "TIME": df5.index[-1].astimezone(IST).strftime('%H:%M'),
                        "STOCK": s, "ACTION": "SELL 🔴 (Resistance)",
                        "PRICE": round(price, 2), "LEVEL": "R1/EMA20",
                        "SL": round(price + atr, 2), "TARGET": round(price - (atr*2.5), 2)
                    })
            except: continue
            
        if pb_list:
            pb_df = pd.DataFrame(pb_list)
            st.table(pb_df)
            st.download_button("📥 Download Excel", data=to_excel(pb_df), file_name="Pullback_Signals.xlsx")
        else: st.info("No Pullback signals found in the last 5 minutes.")

# -----------------------------
# 3. HISTORY LOGS
# -----------------------------
with tab3:
    bt_date = st.date_input("Select Date", value=now.date() - timedelta(days=1))
    if st.button("SHOW FULL DAY LOG"):
        logs = []
        for s in stocks:
            try:
                df = add_indicators(data_5m[s + ".NS"].dropna())
                df.index = df.index.tz_convert(IST)
                df_day = df[df.index.date == bt_date]
                if df_day.empty: continue
                
                for i in range(10, len(df_day)):
                    row = df_day.iloc[i]
                    if abs(row['Close'] - row['EMA20']) / row['EMA20'] < 0.004:
                        logs.append({
                            "TIME": df_day.index[i].strftime('%H:%M'),
                            "STOCK": s, "PRICE": round(row['Close'], 2),
                            "TYPE": "PULLBACK", "RSI": round(row['RSI'], 1)
                        })
            except: continue
        if logs: st.dataframe(pd.DataFrame(logs), use_container_width=True)
        else: st.warning("No data found.")
