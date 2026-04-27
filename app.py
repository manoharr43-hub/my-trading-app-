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
st.set_page_config(page_title="🚀 NSE AI PRO V26", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V26 - SUPPORT PULLBACK & PIVOT EDITION")
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
# CORE INDICATORS (V26 UPDATED)
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
    
    # Pivot Points (Daily calculation for Support/Resistance)
    if interval == '1d':
        df['PP'] = (df['High'] + df['Low'] + df['Close']) / 3
        df['R1'] = (2 * df['PP']) - df['Low']
        df['S1'] = (2 * df['PP']) - df['High']
        df['R2'] = df['PP'] + (df['High'] - df['Low'])
        df['S2'] = df['PP'] - (df['High'] - df['Low'])
        
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
        df.to_excel(writer, index=False, sheet_name='Data')
    return output.getvalue()

# =============================
# TABS
# =============================
tab1, tab2, tab3 = st.tabs(["🔍 MASTER SCANNER", "🎯 SUPPORT PULLBACKS", "📊 BACKTEST REPORT"])

# -----------------------------
# 1. MASTER SCANNER (Buy/Sell/BigPlayers)
# -----------------------------
with tab1:
    if st.button("RUN MASTER SCAN"):
        res = []
        for s in stocks:
            try:
                df1 = add_indicators(data_1d[s + ".NS"].dropna(), '1d')
                df5 = add_indicators(data_5m[s + ".NS"].dropna(), '5m')
                l1, l5 = df1.iloc[-1], df5.iloc[-1]
                
                big_p = "🔥 YES" if l5['Volume'] > (l5['VolAvg'] * 2) else "-"
                sig = "None"
                if l1['Close'] > l1['EMA20'] and l5['Close'] > l5['VWAP'] and l5['RSI'] > 55: sig = "BUY 🟢"
                elif l1['Close'] < l1['EMA20'] and l5['Close'] < l5['VWAP'] and l5['RSI'] < 45: sig = "SELL 🔴"
                
                if sig != "None":
                    res.append({
                        "TIME": df5.index[-1].astimezone(IST).strftime('%H:%M'),
                        "STOCK": s, "SIGNAL": sig, "BIG_P": big_p,
                        "PRICE": round(l5['Close'], 2),
                        "TARGET": round(l5['Close'] + (l5['ATR']*2) if "BUY" in sig else l5['Close'] - (l5['ATR']*2), 2),
                        "SL": round(l5['Close'] - l5['ATR'] if "BUY" in sig else l5['Close'] + l5['ATR'], 2)
                    })
            except: continue
        if res:
            res_df = pd.DataFrame(res)
            st.dataframe(res_df, use_container_width=True)
            st.download_button("📥 Export CSV", data=to_excel(res_df), file_name="Master_Signals.xlsx")
        else: st.info("Scanning... No strong signals yet.")

# -----------------------------
# 2. SUPPORT PULLBACK SCANNER (S1, S2, EMA20)
# -----------------------------
with tab2:
    if st.button("FIND SUPPORT PULLBACKS"):
        pb_res = []
        for s in stocks:
            try:
                df1 = add_indicators(data_1d[s + ".NS"].dropna(), '1d')
                df5 = add_indicators(data_5m[s + ".NS"].dropna(), '5m')
                l1, l5 = df1.iloc[-2], df5.iloc[-1] # l1 is yesterday's pivots
                
                # Support levels
                s1, ema20 = l1['S1'], l5['EMA20']
                curr_price = l5['Close']
                
                # Check proximity to S1 or EMA20
                near_s1 = abs(curr_price - s1) / s1 < 0.003
                near_ema = abs(curr_price - ema20) / ema20 < 0.004
                
                if (near_s1 or near_ema) and curr_price > l5['Open']:
                    pb_res.append({
                        "TIME": df5.index[-1].astimezone(IST).strftime('%H:%M'),
                        "STOCK": s, "PRICE": round(curr_price, 2),
                        "ZONE": "S1 SUPPORT 🛡️" if near_s1 else "EMA20 PULLBACK 📈",
                        "RSI": round(l5['RSI'], 1)
                    })
            except: continue
        if pb_res: st.table(pd.DataFrame(pb_res))
        else: st.warning("No stocks currently at support levels.")

# -----------------------------
# 3. BACKTEST REPORT (Full Day Logic)
# -----------------------------
with tab3:
    bt_date = st.date_input("Analysis Date", value=now.date() - timedelta(days=1))
    if st.button("EXECUTE BACKTEST"):
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
                    sig = "BUY 🟢" if row['Close'] > row['VWAP'] and row['RSI'] > 60 else ("SELL 🔴" if row['Close'] < row['VWAP'] and row['RSI'] < 40 else "None")
                    
                    if sig != "None" or is_pb:
                        logs.append({
                            "TIME": df_day.index[i].strftime('%H:%M'),
                            "STOCK": s, "TYPE": sig if sig != "None" else "PB",
                            "PRICE": round(row['Close'], 2), "VOL": "🔥" if row['Volume'] > row['VolAvg']*2 else ""
                        })
            except: continue
        if logs:
            log_df = pd.DataFrame(logs)
            st.dataframe(log_df, use_container_width=True)
            st.download_button("📥 Download Report", data=to_excel(log_df), file_name="FullDay_Report.xlsx")
        else: st.error("No data available for selected date.")
