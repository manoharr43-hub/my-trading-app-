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
st.set_page_config(page_title="🚀 NSE AI QUANT PRO V4.5", layout="wide")

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

st.title("🚀 NSE AI QUANT PRO - V4.5")
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
    
    # Intraday VWAP
    df['Date_Only'] = df.index.date
    df['PV'] = df['Close'] * df['Volume']
    df['VWAP'] = df.groupby('Date_Only')['PV'].cumsum() / df.groupby('Date_Only')['Volume'].cumsum()
    
    # Technicals
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-9))))
    
    # ATR & RVOL
    tr = pd.concat([df['High']-df['Low'], abs(df['High']-df['Close'].shift()), abs(df['Low']-df['Close'].shift())], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()
    df['VolAvg'] = df['Volume'].rolling(20).mean()
    df['RVOL'] = df['Volume'] / (df['VolAvg'] + 1e-9)
    
    # Range for Consolidation
    df['High20'] = df['High'].rolling(window=20).max()
    df['Low20'] = df['Low'].rolling(window=20).min()
    df['Range_Width'] = (df['High20'] - df['Low20']) / df['Low20'] * 100
    
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
        nifty_trend = "UP" if nifty_df.iloc[-1]['Close'] > nifty_df.iloc[-2]['Close'] else "DOWN"
        
        ticker = s + ".NS"
        df5 = add_indicators(data_5m[ticker].dropna())
        df15 = add_indicators(data_15m[ticker].dropna())
        
        if len(df5) < 35 or len(df15) < 35: return None
        
        last = df5.iloc[-1]
        trend_15m = "UP" if df15.iloc[-1]['Close'] > df15.iloc[-1]['EMA20'] else "DOWN"
        
        signal, reason = None, ""
        is_cons = last['Range_Width'] < 0.8
        
        if nifty_trend == "UP" and last['Close'] > last['VWAP'] and last['RSI'] > 55 and trend_15m == "UP":
            if is_cons and last['Close'] > df5.iloc[-2]['High20'] and last['RVOL'] > 1.5:
                signal, reason = "BUY", "Consolidation Breakout 🚀"
            elif last['RVOL'] > 2.0:
                signal, reason = "BUY", "Big Player Entry ⚡"
        
        elif nifty_trend == "DOWN" and last['Close'] < last['VWAP'] and last['RSI'] < 45 and trend_15m == "DOWN":
            if is_cons and last['Close'] < df5.iloc[-2]['Low20'] and last['RVOL'] > 1.5:
                signal, reason = "SELL", "Consolidation Breakdown 📉"
            elif last['RVOL'] > 2.0:
                signal, reason = "SELL", "Big Exit/Short 🔴"
                
        if not signal: return None
        
        sl_pts = float(last['ATR'] * 1.5)
        return {
            "STOCK": s, "SIGNAL": signal, "PRICE": round(last['Close'], 2), "REASON": reason,
            "RVOL": round(last['RVOL'], 2), "SL": round(last['Close'] - sl_pts if signal=="BUY" else last['Close'] + sl_pts, 2),
            "TGT": round(last['Close'] + sl_pts*2.5 if signal=="BUY" else last['Close'] - sl_pts*2.5, 2),
            "TIME": last.name.astimezone(IST).strftime('%H:%M')
        }
    except: return None

# ==========================================
# 6. UI & TABS
# ==========================================
tab1, tab2 = st.tabs(["🔴 LIVE PRO SCANNER", "📊 DETAILED BACKTEST"])

with tab1:
    if st.button("🚀 START SCANNING"):
        with st.spinner("Scanning..."):
            with ThreadPoolExecutor(max_workers=20) as executor:
                res = [r for r in list(executor.map(scan_stock, stocks)) if r]
            if res:
                st.dataframe(pd.DataFrame(res), use_container_width=True)
            else: st.info("No Signals Found.")

with tab2:
    st.header("📈 Backtest Analysis (Last 5 Days)")
    if st.button("📊 RUN BACKTEST"):
        all_bt = []
        with st.spinner("Processing History..."):
            for s in stocks:
                try:
                    df = add_indicators(data_5m[s+".NS"].dropna())
                    for i in range(30, len(df)-20):
                        row = df.iloc[i]
                        # Trend Check
                        sig = None
                        if row['RVOL'] > 1.5 and row['RSI'] > 55 and row['Close'] > row['VWAP']: sig = "BUY"
                        elif row['RVOL'] > 1.5 and row['RSI'] < 45 and row['Close'] < row['VWAP']: sig = "SELL"
                        
                        if sig:
                            entry_p = row['Close']
                            sl = entry_p - (row['ATR']*1.5) if sig=="BUY" else entry_p + (row['ATR']*1.5)
                            tp = entry_p + (row['ATR']*2.5) if sig=="BUY" else entry_p - (row['ATR']*2.5)
                            
                            res_bt, exit_t = "OPEN", None
                            for j in range(i+1, min(i+60, len(df))):
                                next_r = df.iloc[j]
                                # Exit Rules
                                if (sig=="BUY" and next_r['Low'] <= sl) or (sig=="SELL" and next_r['High'] >= sl):
                                    res_bt, exit_t = "LOSS", next_r.name; break
                                if (sig=="BUY" and next_r['High'] >= tp) or (sig=="SELL" and next_r['Low'] <= tp):
                                    res_bt, exit_t = "PROFIT", next_r.name; break
                                # EOD Square-off
                                if next_r.name.astimezone(IST).hour >= 15 and next_r.name.astimezone(IST).minute >= 15:
                                    res_bt = "PROFIT" if (sig=="BUY" and next_r['Close'] > entry_p) or (sig=="SELL" and next_r['Close'] < entry_p) else "LOSS"
                                    exit_t = next_r.name; break
                            
                            if res_bt != "OPEN":
                                all_bt.append({
                                    "Stock": s, "Date": row.name.astimezone(IST).strftime('%Y-%m-%d'),
                                    "Signal": sig, "RVOL": round(row['RVOL'], 2), "Entry": round(entry_p, 2),
                                    "Result": res_bt, "Duration": int((exit_t - row.name).total_seconds() / 60)
                                })
                except: continue
        
        if all_bt:
            st.dataframe(pd.DataFrame(all_bt), use_container_width=True)
        else: st.warning("No Trades Found.")
