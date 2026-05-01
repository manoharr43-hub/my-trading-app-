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
st.set_page_config(page_title="🚀 NSE AI PRO V45.0", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V45.0 - NSE 200 FULL SCANNER")
st.write(f"🕒 **Market Time:** {now.strftime('%Y-%m-%d %H:%M:%S')}")

# =============================
# NSE 200 COMPLETE STOCK LIST
# =============================
stocks = [
    "ABB","ACC","ADANIENSOL","ADANIENT","ADANIGREEN","ADANIPORTS","ADANIPOWER","ATGL","ABCAPITAL","ABFRL",
    "ALKEM","AMBUJACEM","APOLLOHOSP","APOLLOTYRE","ASHOKLEY","ASIANPAINT","ASTRAL","AUROPHARMA","AU SMALL FINANCE BANK","AVANTIFEED",
    "AXISBANK","BAJAJ-AUTO","BAJFINANCE","BAJAJFINSV","BAJAJHLDNG","BALKRISIND","BANDHANBNK","BANKBARODA","BANKINDIA","BATAINDIA",
    "BEL","BERGEPAINT","BHARATFORG","BHEL","BPCL","BHARTIARTL","BIOCON","BOSCHLTD","BRITANNIA","BSOFT",
    "CANBK","CGPOWER","CHOLAFIN","CIPLA","COALINDIA","COFORGE","COLPAL","CONCOR","COROMANDEL","CROMPTON",
    "CUMMINSIND","CYIENT","DABUR","DALBHARAT","DEEPAKNTR","DELHIVERY","DIVISLAB","DIXON","DLF","DRREDDY",
    "EICHERMOT","ESCORTS","EXIDEIND","FEDERALBNK","FORTIS","GAIL","GLENMARK","GMRINFRA","GODREJCP","GODREJPROP",
    "GRASIM","GUJGASLTD","HAL","HAVELLS","HCLTECH","HDFCBANK","HDFCLIFE","HEROMOTOCO","HINDALCO","HINDCOPPER",
    "HINDPETRO","HINDUNILVR","ICICIBANK","ICICIGI","ICICIPRULI","IDFCFIRSTB","IDFC","IEX","IGL","INDHOTEL",
    "INDIACEM","INDIAMART","INDIGO","INDUSINDBK","INDUSTOWER","INFY","IOC","IRCTC","IRFC","ITC",
    "JINDALSTEL","JSWENERGY","JSWSTEEL","JUBLFOOD","KOTAKBANK","KPITTECH","L&TFH","LT","LTIM","LTTS",
    "LICHSGFIN","LICI","LUPIN","M&M","M&MFIN","MANAPPURAM","MARICO","MARUTI","MAHABANK","MAXHEALTH",
    "METROPOLIS","MFSL","MGL","MPHASIS","MRF","MUTHOOTFIN","NATIONALUM","NAVINFLUOR","NESTLEIND","NMDC",
    "NTPC","OBEROIRLTY","ONGC","PAGEIND","PAYTM","PEL","PERSISTENT","PETRONET","PFC","PIDILITIND",
    "PIIND","PNB","POLYCAB","POONAWALLA","POWERGRID","PRESTIGE","PVRINOX","RECLTD","RELIANCE","SAIL",
    "SBICARD","SBILIFE","SBIN","SHREECEM","SHRIRAMFIN","SIEMENS","SRF","SUNPHARMA","SUNTV","SYNGENE",
    "TATACOMM","TATACONSUM","TATAELXSI","TATAMOTORS","TATAPOWER","TATASTEEL","TCS","TECHM","TITAN","TORNTPHARM",
    "TRENT","TVSMOTOR","ULTRACEMCO","UBL","UPL","VBL","VEDL","VOLTAS","WIPRO","YESBANK","ZEEL","ZOMATO"
]

# =============================
# CORE INDICATORS LOGIC
# =============================
def add_indicators(df):
    df = df.copy()
    if len(df) < 20: return df
    
    # EMA 20 for Pullback support
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    
    # VWAP with Daily Reset
    df['Date_Only'] = df.index.date
    df['PV'] = df['Close'] * df['Volume']
    df['VWAP'] = df.groupby('Date_Only')['PV'].cumsum() / df.groupby('Date_Only')['Volume'].cumsum()
    
    # ATR for Risk/Reward
    high_low = df['High'] - df['Low']
    tr = pd.concat([high_low, abs(df['High'] - df['Close'].shift()), abs(df['Low'] - df['Close'].shift())], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()
    
    # Volume Avg for Big Player detection
    df['VolAvg'] = df['Volume'].rolling(20).mean()
    
    return df

@st.cache_data(ttl=60)
def fetch_data(symbols, interval, period):
    tickers = [s + ".NS" for s in symbols]
    return yf.download(tickers, period=period, interval=interval, group_by='ticker', progress=False)

with st.spinner("🚀 Scanning NSE 200 Stocks... Please wait."):
    data_5m = fetch_data(stocks, "5m", "5d")

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='NSE_AI_PRO_Report')
    return output.getvalue()

# =============================
# TABS SETUP
# =============================
tab1, tab2 = st.tabs(["🔍 LIVE PULLBACK SCAN", "📊 SMART BACKTEST"])

# -----------------------------
# TAB 1: LIVE SCANNER
# -----------------------------
with tab1:
    if st.button("EXECUTE LIVE NSE 200 SCAN"):
        results = []
        for s in stocks:
            try:
                df_raw = data_5m[s + ".NS"].dropna()
                if df_raw.empty: continue
                df = add_indicators(df_raw)
                l = df.iloc[-1]
                
                # Pullback Distance Logic (0.4% from EMA20)
                dist = abs(l['Close'] - l['EMA20']) / l['EMA20']
                
                if dist < 0.004:
                    signal = "None"
                    if l['Close'] > l['VWAP'] and l['Close'] > l['Open']: signal = "BUY 🟢"
                    elif l['Close'] < l['VWAP'] and l['Close'] < l['Open']: signal = "SELL 🔴"
                    
                    if signal != "None":
                        entry = round(l['Close'], 2)
                        results.append({
                            "TIME": df.index[-1].astimezone(IST).strftime('%H:%M'),
                            "STOCK": s, "ACTION": signal,
                            "BIG PLAYER": "🔥 YES" if l['Volume'] > l['VolAvg']*2.5 else "Normal",
                            "PRICE": entry,
                            "SL": round(entry - (l['ATR']*1.5) if "BUY" in signal else entry + (l['ATR']*1.5), 2),
                            "TGT": round(entry + (l['ATR']*3) if "BUY" in signal else entry - (l['ATR']*3), 2)
                        })
            except: continue
        
        if results:
            df_res = pd.DataFrame(results)
            st.dataframe(df_res, use_container_width=True)
            st.download_button("📥 Download Excel", data=to_excel(df_res), file_name=f"Live_Scan_{now.date()}.xlsx")
        else:
            st.info("No pullback signals found in NSE 200 right now.")

# -----------------------------
# TAB 2: BACKTEST (PULLBACK + OUTCOME)
# -----------------------------
with tab2:
    bt_date = st.date_input("Select History Date", value=now.date() - timedelta(days=1))
    if st.button("RUN SMART BACKTEST"):
        bt_logs = []
        for s in stocks:
            try:
                df_raw = data_5m[s + ".NS"].dropna()
                df_raw.index = df_raw.index.tz_convert(IST)
                df_day = add_indicators(df_raw)
                df_day = df_day[df_day.index.date == bt_date]
                
                if df_day.empty: continue

                last_time = None

                for i in range(15, len(df_day)):
                    row = df_day.iloc[i]
                    curr_time = df_day.index[i]
                    
                    # 45-min gap to avoid redundant signals
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
                            
                            # Outcome Logic (Check future candles)
                            outcome = "OPEN"
                            future = df_day.iloc[i+1 : i+25] 
                            for _, f_row in future.iterrows():
                                if "BUY" in sig:
                                    if f_row['High'] >= tgt: outcome = "🎯 TARGET"; break
                                    if f_row['Low'] <= sl: outcome = "🛑 SL"; break
                                else:
                                    if f_row['Low'] <= tgt: outcome = "🎯 TARGET"; break
                                    if f_row['High'] >= sl: outcome = "🛑 SL"; break

                            bt_logs.append({
                                "TIME": curr_time.strftime('%H:%M'),
                                "STOCK": s, "TYPE": sig, "ENTRY": entry,
                                "BIG PLAYER": "🔥" if row['Volume'] > row['VolAvg']*2.5 else "-",
                                "RESULT": outcome
                            })
                            last_time = curr_time
            except: continue
        
        if bt_logs:
            bt_df = pd.DataFrame(bt_logs)
            st.dataframe(bt_df, use_container_width=True)
            st.download_button("📥 Download BT Report", data=to_excel(bt_df), file_name=f"BT_{bt_date}.xlsx")
        else:
            st.warning("No signals found for this date.")
