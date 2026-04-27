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
st.set_page_config(page_title="🚀 NSE AI PRO V25", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V25 - BIG PLAYERS & FULL BACKTEST")
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
# INDICATORS
# =============================
def add_indicators(df):
    df = df.copy()
    if len(df) < 20: return df
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-9)
    
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # ATR
    high_low = df['High'] - df['Low']
    high_close = abs(df['High'] - df['Close'].shift())
    low_close = abs(df['Low'] - df['Close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()
    
    # Volume Avg for Big Players
    df['VolAvg'] = df['Volume'].rolling(20).mean()
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
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()

# =============================
# TABS
# =============================
tab1, tab2, tab3 = st.tabs(["🔍 LIVE SIGNALS (BIG PLAYERS)", "🎯 PULLBACK SCANNER", "📊 FULL DAY BACKTEST"])

# -----------------------------
# 1. LIVE SIGNALS + BIG PLAYERS
# -----------------------------
with tab1:
    if st.button("RUN LIVE SCANNER"):
        res = []
        for s in stocks:
            try:
                df1 = add_indicators(data_1d[s + ".NS"].dropna())
                df5 = add_indicators(data_5m[s + ".NS"].dropna())
                l1, l5 = df1.iloc[-1], df5.iloc[-1]
                
                # Big Players Check (Volume > 2x Avg)
                big_player = "🔥 YES" if l5['Volume'] > (l5['VolAvg'] * 2) else "No"
                
                # Signal Logic
                signal = "None"
                if l1['Close'] > l1['EMA20'] and l5['Close'] > l5['VWAP'] and l5['RSI'] > 55:
                    signal = "BUY 🟢"
                elif l1['Close'] < l1['EMA20'] and l5['Close'] < l5['VWAP'] and l5['RSI'] < 45:
                    signal = "SELL 🔴"
                
                if signal != "None":
                    res.append({
                        "TIME": df5.index[-1].astimezone(IST).strftime('%H:%M:%S'),
                        "STOCK": s, "SIGNAL": signal,
                        "BIG PLAYER": big_player,
                        "ENTRY": round(l5['Close'], 2),
                        "SL": round(l5['Close'] - l5['ATR'] if signal == "BUY 🟢" else l5['Close'] + l5['ATR'], 2),
                        "TARGET": round(l5['Close'] + l5['ATR']*2 if signal == "BUY 🟢" else l5['Close'] - l5['ATR']*2, 2)
                    })
            except: continue
        if res:
            df_res = pd.DataFrame(res)
            st.dataframe(df_res, use_container_width=True)
            st.download_button("📥 Download Excel", data=to_excel(df_res), file_name="Live_Signals.xlsx")
        else: st.info("No active signals found.")

# -----------------------------
# 2. PULLBACK SCANNER (Fix Time)
# -----------------------------
with tab2:
    if st.button("SCAN PULLBACKS"):
        pb_res = []
        for s in stocks:
            try:
                df5 = add_indicators(data_5m[s + ".NS"].dropna())
                l = df5.iloc[-1]
                dist = abs(l['Close'] - l['EMA20']) / l['EMA20']
                
                if dist < 0.005:
                    pb_res.append({
                        "TIME": df5.index[-1].astimezone(IST).strftime('%H:%M:%S'),
                        "STOCK": s, "PRICE": round(l['Close'], 2),
                        "EMA20": round(l['EMA20'], 2),
                        "STATUS": "TOUCHING 🎯" if dist < 0.001 else "NEAR 🔔"
                    })
            except: continue
        if pb_res:
            st.dataframe(pd.DataFrame(pb_res), use_container_width=True)
        else: st.info("No pullbacks at this moment.")

# -----------------------------
# 3. FULL DAY BACKTEST (Buy/Sell + Pullback)
# -----------------------------
with tab3:
    bt_date = st.date_input("Select Backtest Date", value=now.date() - timedelta(days=1))
    if st.button("RUN FULL DAY ANALYSIS"):
        all_day_logs = []
        for s in stocks:
            try:
                df = add_indicators(data_5m[s + ".NS"].dropna())
                df.index = df.index.tz_convert(IST)
                df_day = df[df.index.date == bt_date]
                
                if df_day.empty: continue

                for i in range(10, len(df_day)):
                    row = df_day.iloc[i]
                    # Pullback Logic
                    is_pb = abs(row['Close'] - row['EMA20']) / row['EMA20'] < 0.004
                    # Buy/Sell Logic
                    sig = "None"
                    if row['Close'] > row['VWAP'] and row['RSI'] > 60: sig = "BUY 🟢"
                    elif row['Close'] < row['VWAP'] and row['RSI'] < 40: sig = "SELL 🔴"
                    
                    if sig != "None" or is_pb:
                        all_day_logs.append({
                            "TIME": df_day.index[i].strftime('%H:%M'),
                            "STOCK": s,
                            "PRICE": round(row['Close'], 2),
                            "TYPE": sig if sig != "None" else "PULLBACK 🎯",
                            "BIG PLAYER": "🔥" if row['Volume'] > row['VolAvg']*2 else "-"
                        })
            except: continue
            
        if all_day_logs:
            bt_df = pd.DataFrame(all_day_logs)
            st.dataframe(bt_df, use_container_width=True) # Full day data show
            st.download_button("📥 Download Full Backtest", data=to_excel(bt_df), file_name="Full_Day_Backtest.xlsx")
        else: st.warning("No data found for this date.")
