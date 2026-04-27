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
st.set_page_config(page_title="🚀 NSE AI PRO V39", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V39 - ALL-IN-ONE SCANNER & BACKTEST")
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
# INDICATORS (V39)
# =============================
def add_indicators(df):
    df = df.copy()
    if len(df) < 20: return df
    
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-9)
    
    # ATR for SL/Target
    high_low = df['High'] - df['Low']
    tr = pd.concat([high_low, abs(df['High'] - df['Close'].shift()), abs(df['Low'] - df['Close'].shift())], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()
    
    # Volume for Big Players
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
        df.to_excel(writer, index=False, sheet_name='Report')
    return output.getvalue()

# =============================
# TABS
# =============================
tab1, tab2 = st.tabs(["🚀 LIVE SCANNER", "📊 BACKTEST (FULL DETAILS)"])

# -----------------------------
# TAB 1: LIVE SCANNER
# -----------------------------
with tab1:
    if st.button("RUN LIVE SCAN"):
        live_res = []
        for s in stocks:
            try:
                df = add_indicators(data_5m[s + ".NS"].dropna())
                l = df.iloc[-1]
                dist = abs(l['Close'] - l['EMA20']) / l['EMA20']
                
                if dist < 0.004:
                    signal = "None"
                    if l['Close'] > l['VWAP'] and l['Close'] > l['Open']: signal = "BUY 🟢"
                    elif l['Close'] < l['VWAP'] and l['Close'] < l['Open']: signal = "SELL 🔴"
                    
                    if signal != "None":
                        atr = l['ATR']
                        entry = round(l['Close'], 2)
                        live_res.append({
                            "TIME": df.index[-1].astimezone(IST).strftime('%H:%M'),
                            "STOCK": s, "SIGNAL": signal,
                            "BIG PLAYER": "🔥 YES" if l['Volume'] > l['VolAvg']*2.5 else "-",
                            "ENTRY": entry,
                            "STOP LOSS": round(entry - (atr*1.5) if "BUY" in signal else entry + (atr*1.5), 2),
                            "TARGET": round(entry + (atr*3) if "BUY" in signal else entry - (atr*3), 2)
                        })
            except: continue
        if live_res: st.table(pd.DataFrame(live_res))
        else: st.info("No active signals.")

# -----------------------------
# TAB 2: BACKTEST (FULL DETAILS & REVERSAL)
# -----------------------------
with tab2:
    bt_date = st.date_input("Select Date", value=now.date() - timedelta(days=1))
    if st.button("RUN DETAILED BACKTEST"):
        bt_results = []
        for s in stocks:
            try:
                df = data_5m[s + ".NS"].dropna()
                df.index = df.index.tz_convert(IST)
                df_day = add_indicators(df[df.index.date == bt_date])
                if df_day is None or df_day.empty: continue

                last_action, last_time = None, None

                for i in range(15, len(df_day)):
                    row = df_day.iloc[i]
                    curr_time = df_day.index[i]
                    dist = abs(row['Close'] - row['EMA20']) / row['EMA20']
                    
                    if dist < 0.004:
                        curr_sig = "None"
                        if row['Close'] > row['VWAP'] and row['Close'] > row['Open']: curr_sig = "BUY 🟢"
                        elif row['Close'] < row['VWAP'] and row['Close'] < row['Open']: curr_sig = "SELL 🔴"
                        
                        if curr_sig != "None":
                            # Reversal logic: Trend maarithe chupinchali
                            if curr_sig != last_action or (last_time and (curr_time - last_time) > timedelta(minutes=45)):
                                entry = round(row['Close'], 2)
                                atr = row['ATR']
                                bt_results.append({
                                    "TIME": curr_time.strftime('%H:%M'),
                                    "STOCK": s, "ACTION": curr_sig,
                                    "BIG PLAYER": "🔥" if row['Volume'] > row['VolAvg']*2.5 else "-",
                                    "ENTRY": entry,
                                    "SL": round(entry - (atr*1.5) if "BUY" in curr_sig else entry + (atr*1.5), 2),
                                    "TARGET": round(entry + (atr*3) if "BUY" in curr_sig else entry - (atr*3), 2)
                                })
                                last_action, last_time = curr_sig, curr_time
            except: continue
            
        if bt_results:
            bt_df = pd.DataFrame(bt_results)
            st.dataframe(bt_df, use_container_width=True)
            st.download_button("📥 Excel Download", data=to_excel(bt_df), file_name=f"Detailed_BT_{bt_date}.xlsx")
        else: st.warning("No signals found.")
