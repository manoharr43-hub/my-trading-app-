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
st.set_page_config(page_title="🚀 NSE AI PRO V33", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V33 - CLEAN PULLBACK SYSTEM")
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
    
    return df

@st.cache_data(ttl=60)
def fetch_data(symbols, interval, period):
    tickers = [s + ".NS" for s in symbols]
    return yf.download(tickers, period=period, interval=interval, group_by='ticker', progress=False)

data_5m = fetch_data(stocks, "5m", "5d")

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Backtest')
    return output.getvalue()

# =============================
# TABS
# =============================
tab1, tab2 = st.tabs(["🚀 LIVE PULLBACK", "📊 BACKTEST PULLBACK (FIXED)"])

# -----------------------------
# TAB 1: LIVE PULLBACK
# -----------------------------
with tab1:
    if st.button("SCAN LIVE"):
        res = []
        for s in stocks:
            try:
                df = add_indicators(data_5m[s + ".NS"].dropna())
                l = df.iloc[-1]
                dist = abs(l['Close'] - l['EMA20']) / l['EMA20']
                
                if dist < 0.004:
                    # Buy vs Sell logic
                    action = "BUY 🟢 (Support)" if l['Close'] > l['Open'] else "SELL 🔴 (Resistance)"
                    res.append({
                        "TIME": df.index[-1].astimezone(IST).strftime('%H:%M'),
                        "STOCK": s, "ACTION": action, "PRICE": round(l['Close'], 2),
                        "BIG PLAYER": "🔥" if l['Volume'] > l['VolAvg']*2 else "-"
                    })
            except: continue
        if res: st.table(pd.DataFrame(res))
        else: st.info("No Pullback signals found.")

# -----------------------------
# TAB 2: BACKTEST PULLBACK (ADDED)
# -----------------------------
with tab2:
    bt_date = st.date_input("Select Date", value=now.date() - timedelta(days=1))
    if st.button("RUN BACKTEST PULLBACKS"):
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
                        # Identify Type
                        pb_type = "BUY PULLBACK 🟢" if row['Close'] > row['Open'] else "SELL PULLBACK 🔴"
                        bt_res.append({
                            "TIME": df_day.index[i].strftime('%H:%M'),
                            "STOCK": s, 
                            "TYPE": pb_type, 
                            "PRICE": round(row['Close'], 2),
                            "VOL SPIKE": "🔥" if row['Volume'] > row['VolAvg']*2 else "-"
                        })
            except: continue
        
        if bt_res:
            bt_df = pd.DataFrame(bt_res)
            st.dataframe(bt_df, use_container_width=True)
            st.download_button("📥 Excel Download", data=to_excel(bt_df), file_name=f"Pullback_BT_{bt_date}.xlsx")
        else:
            st.warning("No Pullback data for this date.")
