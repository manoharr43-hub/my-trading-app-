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
st.set_page_config(page_title="🚀 NSE AI PRO V29", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V29 - LIVE SIGNAL MASTER")
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
# INDICATORS (V29)
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
    
    # Big Player Analysis (Volume Avg)
    df['VolAvg'] = df['Volume'].rolling(20).mean()
    
    # Daily Pivot Points
    if interval == '1d':
        df['PP'] = (df['High'] + df['Low'] + df['Close']) / 3
        df['S1'] = (2 * df['PP']) - df['High']
        df['R1'] = (2 * df['PP']) - df['Low']
        
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
        df.to_excel(writer, index=False, sheet_name='Scanner_Data')
    return output.getvalue()

# =============================
# TABS
# =============================
tab1, tab2, tab3 = st.tabs(["🚀 LIVE SCANNER (ALL-IN-ONE)", "🎯 PULLBACK DETECTOR", "📊 BACKTEST LOGS"])

# -----------------------------
# 1. LIVE SCANNER (Buy/Sell/SL/Target/BigPlayer)
# -----------------------------
with tab1:
    if st.button("RUN LIVE SCANNER"):
        live_res = []
        for s in stocks:
            try:
                df1 = add_indicators(data_1d[s + ".NS"].dropna(), '1d')
                df5 = add_indicators(data_5m[s + ".NS"].dropna(), '5m')
                l1, l5 = df1.iloc[-1], df5.iloc[-1]
                
                curr_p = round(l5['Close'], 2)
                atr = l5['ATR']
                
                # Big Player Spike
                big_p = "🔥 BIG ENTRY" if l5['Volume'] > (l5['VolAvg'] * 2.5) else "-"
                
                # BUY Signal Logic
                signal = "WAIT ⏳"
                sl, tgt = 0.0, 0.0
                
                if curr_p > l5['VWAP'] and curr_p > l5['EMA20'] and l5['RSI'] > 55:
                    signal = "BUY 🟢"
                    sl = round(curr_p - (atr * 1.5), 2)
                    tgt = round(curr_p + (atr * 3), 2)
                
                # SELL Signal Logic
                elif curr_p < l5['VWAP'] and curr_p < l5['EMA20'] and l5['RSI'] < 45:
                    signal = "SELL 🔴"
                    sl = round(curr_p + (atr * 1.5), 2)
                    tgt = round(curr_p - (atr * 3), 2)
                
                if signal != "WAIT ⏳":
                    live_res.append({
                        "TIME": df5.index[-1].astimezone(IST).strftime('%H:%M'),
                        "STOCK": s,
                        "SIGNAL": signal,
                        "BIG PLAYER": big_p,
                        "ENTRY": curr_p,
                        "STOP LOSS": sl,
                        "TARGET": tgt,
                        "RSI": round(l5['RSI'], 1)
                    })
            except: continue
            
        if live_res:
            live_df = pd.DataFrame(live_res)
            st.table(live_df) # స్పష్టంగా కనిపించడానికి Table వాడాను
            st.download_button("📥 Download Excel Report", data=to_excel(live_df), file_name="Live_Signals.xlsx")
        else:
            st.info("No active Buy/Sell signals based on current criteria.")

# -----------------------------
# 2. PULLBACK DETECTOR (V28 Logic)
# -----------------------------
with tab2:
    if st.button("SCAN PULLBACKS"):
        pb_res = []
        for s in stocks:
            try:
                df5 = add_indicators(data_5m[s + ".NS"].dropna())
                l = df5.iloc[-1]
                dist = abs(l['Close'] - l['EMA20']) / l['EMA20']
                if dist < 0.004:
                    pb_res.append({
                        "TIME": df5.index[-1].astimezone(IST).strftime('%H:%M'),
                        "STOCK": s, "PRICE": round(l['Close'], 2),
                        "TYPE": "SUPPORT PULLBACK" if l['Close'] > l['Open'] else "RESISTANCE PB",
                        "RSI": round(l['RSI'], 1)
                    })
            except: continue
        st.dataframe(pd.DataFrame(pb_res), use_container_width=True)

# -----------------------------
# 3. BACKTEST
# -----------------------------
with tab3:
    bt_date = st.date_input("Backtest Date", value=now.date() - timedelta(days=1))
    if st.button("RUN HISTORY"):
        # V28 లోని బ్యాక్‌టెస్ట్ లాజిక్ ఇక్కడ ఉంటుంది
        st.write("Processing full day data...")
