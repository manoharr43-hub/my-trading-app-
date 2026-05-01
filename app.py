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
st.set_page_config(page_title="🚀 NSE AI PRO V44.0", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V44.0 - MASTER PULLBACK")
st.write(f"🕒 **Market Time:** {now.strftime('%Y-%m-%d %H:%M:%S')}")

# =============================
# NSE 200 STOCK LIST
# =============================
stocks = [ 
    "RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","AXISBANK","KOTAKBANK","LT","ITC",
    "HINDUNILVR","ASIANPAINT","MARUTI","SUNPHARMA","ONGC","NTPC","POWERGRID","TATASTEEL",
    "JSWSTEEL","BAJFINANCE","BAJAJFINSV","ADANIENT","ADANIPORTS","ULTRACEMCO","GRASIM",
    "TECHM","WIPRO","HCLTECH","NESTLEIND","BRITANNIA","CIPLA","DIVISLAB","DRREDDY","BPCL",
    "IOC","BHARTIARTL","TITAN","M&M","HEROMOTOCO","EICHERMOT","TATAMOTORS","COALINDIA",
    "SHREECEM","HAVELLS","SIEMENS","TORNTPHARM","PIDILITIND","LTIM","BEL","DLF",
    "INDUSINDBK","PNB","BANKBARODA","CANBK","FEDERALBNK","IDFCFIRSTB","YESBANK","ZEEL","ZOMATO" 
]

# =============================
# IMPROVED INDICATORS (DAILY VWAP RESET)
# =============================
def add_indicators(df):
    df = df.copy()
    if len(df) < 20: return df
    
    # EMA 20
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    
    # Daily Reset VWAP (More accurate for Intraday)
    df['Date_Only'] = df.index.date
    df['PV'] = df['Close'] * df['Volume']
    df['VWAP'] = df.groupby('Date_Only')['PV'].cumsum() / df.groupby('Date_Only')['Volume'].cumsum()
    
    # ATR & Volume Avg
    high_low = df['High'] - df['Low']
    tr = pd.concat([high_low, abs(df['High'] - df['Close'].shift()), abs(df['Low'] - df['Close'].shift())], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()
    df['VolAvg'] = df['Volume'].rolling(20).mean()
    
    return df

@st.cache_data(ttl=60)
def fetch_data(symbols, interval, period):
    tickers = [s + ".NS" for s in symbols]
    data = yf.download(tickers, period=period, interval=interval, group_by='ticker', progress=False)
    return data

with st.spinner("🚀 Syncing NSE 200 Data..."):
    # Pulling 5 days to ensure enough data for EMA/VWAP
    data_5m = fetch_data(stocks, "5m", "5d")

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Report')
        workbook = writer.book
        worksheet = writer.sheets['Report']
        header_format = workbook.add_format({'bold': True, 'bg_color': '#CFE2F3', 'border': 1})
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
    return output.getvalue()

# =============================
# TABS
# =============================
tab1, tab2 = st.tabs(["🔍 LIVE SCANNER", "📊 SMART BACKTEST"])

# -----------------------------
# TAB 1: LIVE SCANNER
# -----------------------------
with tab1:
    if st.button("RUN LIVE SCAN"):
        results = []
        for s in stocks:
            try:
                df_raw = data_5m[s + ".NS"].dropna()
                if df_raw.empty: continue
                
                df = add_indicators(df_raw)
                l = df.iloc[-1]
                
                # Logic: Price near EMA20 (within 0.4%)
                dist = abs(l['Close'] - l['EMA20']) / l['EMA20']
                
                if dist < 0.004:
                    signal = "None"
                    if l['Close'] > l['VWAP'] and l['Close'] > l['Open']: signal = "BUY 🟢"
                    elif l['Close'] < l['VWAP'] and l['Close'] < l['Open']: signal = "SELL 🔴"
                    
                    if signal != "None":
                        entry = round(l['Close'], 2)
                        results.append({
                            "TIME": df.index[-1].astimezone(IST).strftime('%H:%M'),
                            "STOCK": s,
                            "ACTION": signal,
                            "VOL": "🔥 HIGH" if l['Volume'] > l['VolAvg']*2.5 else "Normal",
                            "ENTRY": entry,
                            "SL": round(entry - (l['ATR']*1.5) if "BUY" in signal else entry + (l['ATR']*1.5), 2),
                            "TGT": round(entry + (l['ATR']*3) if "BUY" in signal else entry - (l['ATR']*3), 2)
                        })
            except: continue
        
        if results:
            df_live = pd.DataFrame(results)
            st.dataframe(df_live.style.highlight_max(axis=0, subset=['ENTRY']), use_container_width=True)
            st.download_button("📥 Download Excel", data=to_excel(df_live), file_name=f"Live_{now.date()}.xlsx")
        else:
            st.info("No pullback signals at this moment.")

# -----------------------------
# TAB 2: SMART BACKTEST (P&L TRACKING)
# -----------------------------
with tab2:
    bt_date = st.date_input("Backtest Date", value=now.date() - timedelta(days=1))
    
    if st.button("START BACKTEST"):
        bt_logs = []
        for s in stocks:
            try:
                df_raw = data_5m[s + ".NS"].dropna()
                df_raw.index = df_raw.index.tz_convert(IST)
                
                df_full = add_indicators(df_raw)
                df_day = df_full[df_full.index.date == bt_date]
                
                if df_day.empty: continue

                last_time = None

                for i in range(15, len(df_day)):
                    row = df_day.iloc[i]
                    curr_time = df_day.index[i]
                    
                    # 45-min gap to avoid multiple signals for same trend
                    if last_time and (curr_time - last_time) < timedelta(minutes=45):
                        continue
                        
                    dist = abs(row['Close'] - row['EMA20']) / row['EMA20']
                    
                    if dist < 0.004:
                        sig = "None"
                        if row['Close'] > row['VWAP'] and row['Close'] > row['Open']: sig = "BUY 🟢"
                        elif row['Close'] < row['VWAP'] and row['Close'] < row['Open']: sig = "SELL 🔴"
                        
                        if sig != "None":
                            entry = round(row['Close'], 2)
                            sl = round(entry - (row['ATR']*1.5) if "BUY" in sig else entry + (row['ATR']*1.5), 2)
                            tgt = round(entry + (row['ATR']*3) if "BUY" in sig else entry - (row['ATR']*3), 2)
                            
                            # SIMPLE P&L CHECK (Looking at future candles)
                            outcome = "OPEN"
                            future_data = df_day.iloc[i+1 : i+20] # Check next 20 candles (100 mins)
                            for _, f_row in future_data.iterrows():
                                if "BUY" in sig:
                                    if f_row['High'] >= tgt: outcome = "🎯 TARGET HIT"; break
                                    if f_row['Low'] <= sl: outcome = "🛑 SL HIT"; break
                                else:
                                    if f_row['Low'] <= tgt: outcome = "🎯 TARGET HIT"; break
                                    if f_row['High'] >= sl: outcome = "🛑 SL HIT"; break

                            bt_logs.append({
                                "TIME": curr_time.strftime('%H:%M'),
                                "STOCK": s, "TYPE": sig, "ENTRY": entry,
                                "SL": sl, "TGT": tgt, "RESULT": outcome
                            })
                            last_time = curr_time
            except: continue
        
        if bt_logs:
            bt_df = pd.DataFrame(bt_logs)
            st.dataframe(bt_df, use_container_width=True)
            st.download_button("📥 Download Backtest Excel", data=to_excel(bt_df), file_name=f"BT_{bt_date}.xlsx")
        else:
            st.warning("No signals for the selected date.")
