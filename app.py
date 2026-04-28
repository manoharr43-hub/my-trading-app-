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
st.set_page_config(page_title="🚀 NSE AI PRO V43.1", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V43.1 - NSE 200 MASTER PULLBACK")
st.write(f"🕒 **Market Time:** {now.strftime('%Y-%m-%d %H:%M:%S')}")

# =============================
# NSE 200 STOCK LIST
# =============================
stocks = [ "RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","AXISBANK","KOTAKBANK","LT","ITC","HINDUNILVR","ASIANPAINT","MARUTI","SUNPHARMA","ONGC","NTPC","POWERGRID","TATASTEEL","JSWSTEEL","BAJFINANCE","BAJAJFINSV","ADANIENT","ADANIPORTS","ULTRACEMCO","GRASIM","TECHM","WIPRO","HCLTECH","NESTLEIND","BRITANNIA","CIPLA","DIVISLAB","DRREDDY","BPCL","IOC","BHARTIARTL","TITAN","M&M","HEROMOTOCO","EICHERMOT","TATAMOTORS","COALINDIA","SHREECEM","HAVELLS","SIEMENS","TORNTPHARM","PIDILITIND","LTIM","BEL","DLF","INDUSINDBK","PNB","BANKBARODA","CANBK","FEDERALBNK","IDFCFIRSTB","YESBANK","ZEEL","ZOMATO" ]

# =============================
# INDICATORS
# =============================
def add_indicators(df):
    df = df.copy()
    if len(df) < 20: return df
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-9)
    high_low = df['High'] - df['Low']
    tr = pd.concat([high_low, abs(df['High'] - df['Close'].shift()), abs(df['Low'] - df['Close'].shift())], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()
    df['VolAvg'] = df['Volume'].rolling(20).mean()
    return df

@st.cache_data(ttl=60)
def fetch_data(symbols, interval, period):
    tickers = [s + ".NS" for s in symbols]
    return yf.download(tickers, period=period, interval=interval, group_by='ticker', progress=False)

with st.spinner("🚀 Loading NSE 200 Data..."):
    data_5m = fetch_data(stocks, "5m", "5d")

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Pullback_Report')
    return output.getvalue()

# =============================
# TABS
# =============================
tab1, tab2 = st.tabs(["🔍 LIVE PULLBACK SCAN", "📊 BACKTEST & EXCEL"])

# -----------------------------
# TAB 1: LIVE SCANNER + EXCEL
# -----------------------------
with tab1:
    if st.button("RUN LIVE NSE 200 SCAN"):
        results = []
        for s in stocks:
            try:
                df_raw = data_5m.get(s + ".NS")
                if df_raw is None or df_raw.empty: continue
                
                df = add_indicators(df_raw.dropna())
                l = df.iloc[-1]
                dist = abs(l['Close'] - l['EMA20']) / l['EMA20']
                
                if dist < 0.004:
                    signal = "None"
                    if l['Close'] > l['VWAP'] and l['Close'] > l['Open']: signal = "BUY PULLBACK 🟢"
                    elif l['Close'] < l['VWAP'] and l['Close'] < l['Open']: signal = "SELL PULLBACK 🔴"
                    
                    if signal != "None":
                        entry = round(l['Close'], 2)
                        results.append({
                            "TIME": df.index[-1].astimezone(IST).strftime('%H:%M'),
                            "STOCK": s, "ACTION": signal,
                            "BIG PLAYER": "🔥 YES" if l['Volume'] > l['VolAvg']*2.5 else "-",
                            "ENTRY": entry,
                            "SL": round(entry - (l['ATR']*1.5) if "BUY" in signal else entry + (l['ATR']*1.5), 2),
                            "TGT": round(entry + (l['ATR']*3) if "BUY" in signal else entry - (l['ATR']*3), 2)
                        })
            except: continue
        
        if results:
            df_live = pd.DataFrame(results)
            st.table(df_live)
            st.download_button(
                "📥 Download Live Scan Excel",
                data=to_excel(df_live),
                file_name=f"LiveScan_{now.strftime('%Y%m%d_%H%M')}.xlsx"
            )
        else:
            st.info("No pullback signals found in NSE 200 right now.")

# -----------------------------
# TAB 2: BACKTEST (PULLBACK + EXCEL)
# -----------------------------
with tab2:
    bt_date = st.date_input("Select History Date", value=now.date() - timedelta(days=1))
    if st.button("EXECUTE BACKTEST"):
        bt_logs = []
        for s in stocks:
            try:
                df_raw = data_5m.get(s + ".NS")
                if df_raw is None: continue
                df = df_raw.dropna().copy()
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
                            if curr_sig != last_action or (last_time and (curr_time - last_time) > timedelta(minutes=45)):
                                entry = round(row['Close'], 2)
                                bt_logs.append({
                                    "TIME": curr_time.strftime('%H:%M'),
                                    "STOCK": s, "TYPE": curr_sig, "PRICE": entry,
                                    "BIG PLAYER": "🔥" if row['Volume'] > row['VolAvg']*2.5 else "-",
                                    "SL": round(entry - (row['ATR']*1.5) if "BUY" in curr_sig else entry + (row['ATR']*1.5), 2),
                                    "TGT": round(entry + (row['ATR']*3) if "BUY" in curr_sig else entry - (row['ATR']*3), 2)
                                })
                                last_action, last_time = curr_sig, curr_time
            except: continue
        
        if bt_logs:
            bt_df = pd.DataFrame(bt_logs)
            st.dataframe(bt_df, use_container_width=True)
            st.download_button("📥 Download Excel Report", data=to_excel(bt_df), file_name=f"Backtest_{bt_date}.xlsx")
        else: st.warning("No signals found for this date.")
