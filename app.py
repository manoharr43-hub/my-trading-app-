import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from concurrent.futures import ThreadPoolExecutor
import io

# ==========================================
# 1. CONFIG & TIMEZONE SETUP
# ==========================================
st.set_page_config(page_title="🚀 NSE AI QUANT PRO V4.1", layout="wide")

IST = pytz.timezone("Asia/Kolkata")

def get_now_ist():
    return datetime.now(IST)

now = get_now_ist()

# UI Styling
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1f2937; padding: 15px; border-radius: 10px; border: 1px solid #374151; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 NSE AI QUANT PRO - V4.1")
st.subheader(f"📅 {now.strftime('%d-%b-%Y')} | 🕒 {now.strftime('%H:%M:%S')} IST")

# ==========================================
# 2. STOCKS LIST
# ==========================================
stocks = [
    "ABB","ACC","ADANIENSOL","ADANIENT","ADANIGREEN","ADANIPORTS","ADANIPOWER","ATGL","ABCAPITAL","ABFRL",
    "ALKEM","AMBUJACEM","APOLLOHOSP","APOLLOTYRE","ASHOKLEY","ASIANPAINT","ASTRAL","AUROPHARMA","AUBANK",
    "AXISBANK","BAJAJ-AUTO","BAJFINANCE","BAJAJFINSV","BAJAJHLDNG","BALKRISIND","BANDHANBNK","BANKBARODA",
    "BEL","BERGEPAINT","BHARATFORG","BHEL","BPCL","BHARTIARTL","BIOCON","BOSCHLTD","BRITANNIA","BSOFT",
    "CANBK","CGPOWER","CHOLAFIN","CIPLA","COALINDIA","COFORGE","COLPAL","CONCOR","COROMANDEL","CROMPTON",
    "CUMMINSIND","CYIENT","DABUR","DALBHARAT","DEEPAKNTR","DELHIVERY","DIVISLAB","DIXON","DLF","DRREDDY",
    "EICHERMOT","ESCORTS","EXIDEIND","FEDERALBNK","FORTIS","GAIL","GLENMARK","GMRINFRA","GODREJCP","GODREJPROP",
    "GRASIM","GUJGASLTD","HAL","HAVELLS","HCLTECH","HDFCBANK","HDFCLIFE","HEROMOTOCO","HINDALCO","HINDCOPPER",
    "HINDPETRO","HINDUNILVR","ICICIBANK","ICICIGI","ICICIPRULI","IDFCFIRSTB","IEX","IGL","INDHOTEL",
    "INDIGO","INDUSINDBK","INDUSTOWER","INFY","IOC","IRCTC","IRFC","ITC",
    "JINDALSTEL","JSWENERGY","JSWSTEEL","JUBLFOOD","KOTAKBANK","KPITTECH","L&TFH","LT","LTIM","LTTS",
    "LICHSGFIN","LICI","LUPIN","M&M","M&MFIN","MANAPPURAM","MARICO","MARUTI","MAXHEALTH",
    "METROPOLIS","MFSL","MGL","MPHASIS","MRF","MUTHOOTFIN","NATIONALUM","NESTLEIND","NMDC",
    "NTPC","OBEROIRLTY","ONGC","PAYTM","PEL","PERSISTENT","PETRONET","PFC","PIDILITIND",
    "PIIND","PNB","POLYCAB","POONAWALLA","POWERGRID","PRESTIGE","PVRINOX","RECLTD","RELIANCE","SAIL",
    "SBICARD","SBILIFE","SBIN","SHREECEM","SHRIRAMFIN","SIEMENS","SRF","SUNPHARMA","SUNTV","SYNGENE",
    "TATACOMM","TATACONSUM","TATAELXSI","TATAMOTORS","TATAPOWER","TATASTEEL","TCS","TECHM","TITAN","TORNTPHARM",
    "TRENT","TVSMOTOR","ULTRACEMCO","UBL","UPL","VBL","VEDL","VOLTAS","WIPRO","YESBANK","ZEEL","ZOMATO"
]

# ==========================================
# 3. CORE INDICATORS ENGINE
# ==========================================
def add_indicators(df):
    df = df.copy()
    if df.empty: return df
    
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-9))))
    
    df['Date_Only'] = df.index.date
    df['PV'] = df['Close'] * df['Volume']
    df['VWAP'] = df.groupby('Date_Only')['PV'].cumsum() / df.groupby('Date_Only')['Volume'].cumsum()
    
    tr = pd.concat([df['High']-df['Low'], abs(df['High']-df['Close'].shift()), abs(df['Low']-df['Close'].shift())], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()
    
    df['VolAvg'] = df['Volume'].rolling(20).mean()
    df['RVOL'] = df['Volume'] / (df['VolAvg'] + 1e-9)
    
    df['High20'] = df['High'].rolling(window=20).max()
    df['Low20'] = df['Low'].rolling(window=20).min()
    df['Range_Width'] = (df['High20'] - df['Low20']) / df['Low20'] * 100
    
    df['S_Level'] = df['Low'].rolling(window=30).min()
    df['R_Level'] = df['High'].rolling(window=30).max()
    return df

# ==========================================
# 4. DATA LOADER
# ==========================================
@st.cache_data(ttl=60)
def fetch_all_data(interval):
    tickers = [s + ".NS" for s in stocks] + ["^NSEI"]
    return yf.download(tickers, period="5d", interval=interval, group_by="ticker", progress=False, threads=True)

data_5m = fetch_all_data("5m")
data_15m = fetch_all_data("15m")

# ==========================================
# 5. SCANNER LOGIC
# ==========================================
def scan_stock(s):
    try:
        nifty_df = data_5m["^NSEI"].dropna()
        n_close = nifty_df.iloc[-1]['Close']
        n_prev = nifty_df.iloc[-2]['Close']
        nifty_trend = "UP" if n_close > n_prev else "DOWN"
        
        ticker = s + ".NS"
        df5 = add_indicators(data_5m[ticker].dropna())
        df15 = add_indicators(data_15m[ticker].dropna())
        
        if len(df5) < 35 or len(df15) < 35: return None
        
        last = df5.iloc[-1]
        prev = df5.iloc[-2]
        trend_15m = "UP" if df15.iloc[-1]['Close'] > df15.iloc[-1]['EMA20'] else "DOWN"
        
        signal = None
        reason = ""
        is_cons = df5.iloc[-2]['Range_Width'] < 0.8
        
        # --- BUY Logic (Nifty must be UP) ---
        if nifty_trend == "UP" and last['Close'] > last['VWAP'] and last['RSI'] > 55 and trend_15m == "UP":
            if is_cons and last['Close'] > df5.iloc[-2]['High20'] and last['RVOL'] > 1.5:
                signal, reason = "BUY", "Consolidation Breakout 🚀"
            elif last['RVOL'] > 2.0:
                signal, reason = "BUY", "Big Player Entry ⚡"
            elif last['Low'] <= last['EMA20'] * 1.002 and last['Close'] > last['EMA20']:
                signal, reason = "BUY", "Pullback Entry 🟢"
        
        # --- SELL Logic (Nifty must be DOWN) ---
        elif nifty_trend == "DOWN" and last['Close'] < last['VWAP'] and last['RSI'] < 45 and trend_15m == "DOWN":
            if is_cons and last['Close'] < df5.iloc[-2]['Low20'] and last['RVOL'] > 1.5:
                signal, reason = "SELL", "Consolidation Breakdown 📉"
            elif last['RVOL'] > 2.0:
                signal, reason = "SELL", "Big Exit/Short 🔴"
            elif last['Close'] < prev['S_Level'] and last['RVOL'] > 1.3:
                signal, reason = "SELL", "Support Breakdown 🔨"
                
        if not signal: return None
        
        entry = round(float(last['Close']), 2)
        sl_pts = float(last['ATR'] * 1.5)
        sl = round(entry - sl_pts if signal == "BUY" else entry + sl_pts, 2)
        tgt = round(entry + (sl_pts * 2.5) if signal == "BUY" else entry - (sl_pts * 2.5), 2)
        qty = int(1000 / sl_pts) if sl_pts > 0 else 0
        
        return {
            "STOCK": s, "SIGNAL": signal, "PRICE": entry, "REASON": reason, "QTY": qty,
            "SL": sl, "TGT": tgt, "RVOL": round(last['RVOL'], 2), 
            "TIME": last.name.astimezone(IST).strftime('%H:%M')
        }
    except: return None

# ==========================================
# 6. UI INTERFACE & TABS
# ==========================================
tab1, tab2 = st.tabs(["🔴 LIVE PRO SCANNER", "📊 DETAILED BACKTEST"])

with tab1:
    try:
        n_df = data_5m["^NSEI"].dropna()
        n_last, n_prev = n_df.iloc[-1]['Close'], n_df.iloc[-2]['Close']
        n_chg = round(((n_last - n_prev)/n_prev)*100, 2)
        col1, col2 = st.columns(2)
        col1.metric("NIFTY 50", f"{round(n_last, 2)}", f"{n_chg}%")
        status_msg = "🟢 Market Bullish: Looking for BUYs" if n_chg >= 0 else "🔴 Market Bearish: Looking for SELLs"
        col2.subheader(status_msg)
    except: st.info("Updating Nifty...")

    if st.button("🚀 START SCANNING"):
        with st.spinner("Scanning 150+ Stocks..."):
            with ThreadPoolExecutor(max_workers=20) as executor:
                res = [r for r in list(executor.map(scan_stock, stocks)) if r]
            if res:
                df_res = pd.DataFrame(res)
                st.dataframe(df_res.style.map(
                    lambda x: 'color: #2ecc71; font-weight: bold' if x == 'BUY' else 'color: #e74c3c; font-weight: bold', 
                    subset=['SIGNAL']
                ), use_container_width=True)
            else:
                st.info("ప్రస్తుతానికి నిఫ్టీ ట్రెండ్‌కు తగిన బలమైన BUY/SELL సిగ్నల్స్ లేవు.")

with tab2:
    st.header("📈 Historical Backtest (5 Days)")
    if st.button("📊 RUN BACKTEST"):
        all_bt = []
        with st.spinner("డేటాను అనలైజ్ చేస్తున్నాను..."):
            for s in stocks:
                try:
                    df = add_indicators(data_5m[s+".NS"].dropna())
                    if len(df) < 50: continue

                    for i in range(30, len(df)-20):
                        row = df.iloc[i]
                        current_time = row.name.astimezone(IST)
                        if current_time.hour == 15 and current_time.minute >= 15: continue

                        # Strategy Check
                        signal_type = None
                        if row['RVOL'] > 1.5 and row['RSI'] > 55 and row['Close'] > row['VWAP']:
                            signal_type = "BUY"
                        elif row['RVOL'] > 1.5 and row['RSI'] < 45 and row['Close'] < row['VWAP']:
                            signal_type = "SELL"

                        if signal_type:
                            entry_p = row['Close']
                            sl_pts = row['ATR'] * 1.5
                            sl_v = entry_p - sl_pts if signal_type == "BUY" else entry_p + sl_pts
                            tp_v = entry_p + (sl_pts * 2.5) if signal_type == "BUY" else entry_p - (sl_pts * 2.5)
                            
                            status, exit_time = "OPEN", None
                            for j in range(i+1, min(i+60, len(df))):
                                check_row = df.iloc[j]
                                check_time = check_row.name.astimezone(IST)
                                
                                # Exit Conditions
                                if signal_type == "BUY":
                                    if check_row['Low'] <= sl_v: status, exit_time = "LOSS", check_row.name; break
                                    if check_row['High'] >= tp_v: status, exit_time = "PROFIT", check_row.name; break
                                else: # SELL
                                    if check_row['High'] >= sl_v: status, exit_time = "LOSS", check_row.name; break
                                    if check_row['Low'] <= tp_v: status, exit_time = "PROFIT", check_row.name; break
                                
                                # Auto Square-off
                                if check_time.hour == 15 and check_time.minute >= 15:
                                    if signal_type == "BUY":
                                        status = "PROFIT" if check_row['Close'] > entry_p else "LOSS"
                                    else:
                                        status = "PROFIT" if check_row['Close'] < entry_p else "LOSS"
                                    exit_time = check_row.name; break
                            
                            if status != "OPEN":
                                e_dt = row.name.astimezone(IST)
                                all_bt.append({
                                    "Stock": s, "Date": e_dt.strftime('%Y-%m-%d'),
                                    "Signal": signal_type, "Time": e_dt.strftime('%H:%M:%S'),
                                    "Entry": round(entry_p, 2), "Result": status,
                                    "Duration": int((exit_time - row.name).total_seconds() / 60)
                                })
                except: continue

        if all_bt:
            bt_df = pd.DataFrame(all_bt)
            st.dataframe(bt_df, use_container_width=True)
        else:
            st.warning("ట్రేడ్స్ ఏవీ దొరకలేదు.")
