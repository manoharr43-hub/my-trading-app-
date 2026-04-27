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
st.set_page_config(page_title="🚀 NSE AI PRO V24", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V24 - TIME & EXCEL UPDATED")
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

# =============================
# EXCEL DOWNLOAD FUNCTION
# =============================
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()

# =============================
# TABS
# =============================
tab1, tab2, tab3 = st.tabs(["🔍 LIVE SCANNER", "🎯 PULLBACK SCAN", "🔥 BACKTEST SYSTEM"])

# -----------------------------
# 1. LIVE SCANNER (With Time)
# -----------------------------
with tab1:
    if st.button("RUN SCANNER"):
        res = []
        for s in stocks:
            try:
                df1 = add_indicators(data_1d[s + ".NS"].dropna())
                df5 = add_indicators(data_5m[s + ".NS"].dropna())
                l1, l5 = df1.iloc[-1], df5.iloc[-1]
                
                if l1['Close'] > l1['EMA20'] and l5['Close'] > l5['VWAP']:
                    res.append({
                        "TIME": df5.index[-1].astimezone(IST).strftime('%H:%M:%S'), # 1. Time Add
                        "STOCK": s, "ENTRY": round(l5['Close'], 2),
                        "SL": round(l5['Close'] - l5['ATR']*1.5, 2),
                        "TARGET": round(l5['Close'] + l5['ATR']*3, 2),
                        "RSI": round(l5['RSI'], 1)
                    })
            except: continue
        if res:
            final_df = pd.DataFrame(res)
            st.dataframe(final_df, use_container_width=True)
            st.download_button("📥 Download Excel", data=to_excel(final_df), file_name="Scanner_Report.xlsx") # 5. Excel
        else: st.info("No stocks found.")

# -----------------------------
# 2. PULLBACK SCAN (With Time)
# -----------------------------
with tab2:
    if st.button("RUN PULLBACK"):
        pb_res = []
        for s in stocks:
            try:
                df5 = add_indicators(data_5m[s + ".NS"].dropna())
                l = df5.iloc[-1]
                dist = abs(l['Close'] - l['EMA20']) / l['EMA20']
                if dist < 0.005 and l['Close'] > l['Open']:
                    pb_res.append({
                        "TIME": df5.index[-1].astimezone(IST).strftime('%H:%M:%S'), # 2. Time Add
                        "STOCK": s, "PRICE": round(l['Close'], 2),
                        "ATR": round(l['ATR'], 2), "RSI": round(l['RSI'], 1)
                    })
            except: continue
        if pb_res:
            pb_df = pd.DataFrame(pb_res)
            st.dataframe(pb_df, use_container_width=True)
            st.download_button("📥 Download Excel", data=to_excel(pb_df), file_name="Pullback_Report.xlsx")
        else: st.info("No pullbacks.")

# -----------------------------
# 3 & 4. BACKTEST (Folder/Pullback fix)
# -----------------------------
with tab3:
    bt_date = st.date_input("Backtest Date", value=now.date() - timedelta(days=1))
    if st.button("START BACKTEST"):
        bt_logs = []
        for s in stocks:
            try:
                df = add_indicators(data_5m[s + ".NS"].dropna())
                # Timezone conversion for matching date
                df.index = df.index.tz_convert(IST)
                df_day = df[df.index.date == bt_date]
                
                if df_day.empty: continue # 3. Folder/Data showing fix

                for i in range(15, len(df_day)-6):
                    snap = df_day.iloc[:i+1]
                    last = snap.iloc[-1]
                    
                    # 4. Pullback backtest logic
                    dist = abs(last['Close'] - last['EMA20']) / last['EMA20']
                    if dist < 0.005:
                        entry = last['Close']
                        future = df_day.iloc[i+1 : i+6]
                        win = any(future['High'] > entry + last['ATR']*2)
                        loss = any(future['Low'] < entry - last['ATR'])
                        
                        res_str = "WIN ✅" if win else ("LOSS ❌" if loss else "HOLD ⚪")
                        bt_logs.append({
                            "TIME": df_day.index[i].strftime('%H:%M'),
                            "STOCK": s, "ENTRY": round(entry, 2), "RESULT": res_str
                        })
                        break
            except: continue
        if bt_logs:
            bt_df = pd.DataFrame(bt_logs)
            st.table(bt_df) # 4. Showing fix
            st.download_button("📥 Download Backtest Excel", data=to_excel(bt_df), file_name="Backtest_Report.xlsx")
        else: st.warning("No signals found for this date.")
