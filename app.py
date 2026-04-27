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
st.set_page_config(page_title="🚀 NSE AI PRO V34", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V34 - PULLBACK TREND FILTER")
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
# INDICATORS (V34)
# =============================
def add_indicators(df):
    df = df.copy()
    if len(df) < 20: return df
    
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-9)
    
    # RSI for Strength
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))
    
    df['VolAvg'] = df['Volume'].rolling(20).mean()
    return df

@st.cache_data(ttl=60)
def fetch_data(symbols, interval, period):
    tickers = [s + ".NS" for s in symbols]
    return yf.download(tickers, period=period, interval=interval, group_by='ticker', progress=False)

data_5m = fetch_data(stocks, "5m", "5d")

# =============================
# TABS
# =============================
tab1, tab2 = st.tabs(["🚀 LIVE FILTERED PULLBACK", "📊 FILTERED BACKTEST"])

# -----------------------------
# TAB 1: LIVE FILTERED
# -----------------------------
with tab1:
    if st.button("RUN FILTERED SCAN"):
        res = []
        for s in stocks:
            try:
                df = add_indicators(data_5m[s + ".NS"].dropna())
                l = df.iloc[-1]
                dist = abs(l['Close'] - l['EMA20']) / l['EMA20']
                
                if dist < 0.004:
                    # ✅ TREND FILTER: VWAP ఆధారంగా Buy/Sell వేరు చేయడం
                    if l['Close'] > l['VWAP'] and l['Close'] > l['Open']:
                        action = "BUY PULLBACK 🟢"
                    elif l['Close'] < l['VWAP'] and l['Close'] < l['Open']:
                        action = "SELL PULLBACK 🔴"
                    else:
                        continue # ట్రెండ్ సరిగ్గా లేకపోతే వదిలేయాలి

                    res.append({
                        "TIME": df.index[-1].astimezone(IST).strftime('%H:%M'),
                        "STOCK": s, "ACTION": action, "PRICE": round(l['Close'], 2),
                        "RSI": round(l['RSI'], 1),
                        "BIG PLAYER": "🔥" if l['Volume'] > l['VolAvg']*2 else "-"
                    })
            except: continue
        if res: st.table(pd.DataFrame(res))
        else: st.info("No Filtered Pullback signals found.")

# -----------------------------
# TAB 2: BACKTEST (FILTERED)
# -----------------------------
with tab2:
    bt_date = st.date_input("Select History Date", value=now.date() - timedelta(days=1))
    if st.button("RUN FILTERED BACKTEST"):
        bt_res = []
        for s in stocks:
            try:
                df = data_5m[s + ".NS"].dropna()
                df.index = df.index.tz_convert(IST)
                df_day = add_indicators(df[df.index.date == bt_date])
                
                if df_day is None or df_day.empty: continue

                for i in range(15, len(df_day)):
                    row = df_day.iloc[i]
                    dist = abs(row['Close'] - row['EMA20']) / row['EMA20']
                    
                    if dist < 0.004:
                        # ✅ TREND FILTER in Backtest
                        if row['Close'] > row['VWAP'] and row['Close'] > row['Open']:
                            pb_type = "BUY PULLBACK 🟢"
                        elif row['Close'] < row['VWAP'] and row['Close'] < row['Open']:
                            pb_type = "SELL PULLBACK 🔴"
                        else:
                            continue

                        bt_res.append({
                            "TIME": df_day.index[i].strftime('%H:%M'),
                            "STOCK": s, "TYPE": pb_type, "PRICE": round(row['Close'], 2),
                            "VOL SPIKE": "🔥" if row['Volume'] > row['VolAvg']*2 else "-"
                        })
            except: continue
        
        if bt_res:
            st.dataframe(pd.DataFrame(bt_res), use_container_width=True)
        else:
            st.warning("No Filtered Pullback data for this date.")
