import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from concurrent.futures import ThreadPoolExecutor
import io

# =============================
# CONFIG & THEME
# =============================
st.set_page_config(page_title="🚀 NSE AI PRO V100 PRO", layout="wide")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1f2937; padding: 15px; border-radius: 10px; border: 1px solid #374151; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 NSE AI PRO V100 - QUANT PRO SYSTEM")

# =============================
# NSE 200 STOCKS
# =============================
stocks = [
    "ABB","ACC","ADANIENSOL","ADANIENT","ADANIGREEN","ADANIPORTS","ADANIPOWER","ATGL","ABCAPITAL","ABFRL",
    "ALKEM","AMBUJACEM","APOLLOHOSP","APOLLOTYRE","ASHOKLEY","ASIANPAINT","ASTRAL","AUROPHARMA","AUBANK","AVANTIFEED",
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
# INDICATORS ENGINE
# =============================
def add_indicators(df):
    df = df.copy()
    if df.empty: return df
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['Date'] = df.index.date
    df['PV'] = df['Close'] * df['Volume']
    df['VWAP'] = df.groupby('Date')['PV'].cumsum() / df.groupby('Date')['Volume'].cumsum()
    tr = pd.concat([df['High']-df['Low'], abs(df['High']-df['Close'].shift()), abs(df['Low']-df['Close'].shift())], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()
    delta = df['Close'].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-9))))
    df['VolAvg'] = df['Volume'].rolling(20).mean()
    df['RVOL'] = df['Volume'] / df['VolAvg']
    return df

# =============================
# DATA FETCHING
# =============================
@st.cache_data(ttl=60)
def fetch_data(interval):
    tickers = [s + ".NS" for s in stocks] + ["^NSEI"]
    return yf.download(tickers, period="5d", interval=interval, group_by="ticker", progress=False)

data_5m = fetch_data("5m")
data_15m = fetch_data("15m")

# =============================
# SIGNALS
# =============================
def get_signal_logic(row, trend_val):
    if row['Close'] > row['VWAP'] and row['RSI'] > 55 and trend_val == "UP" and row['RVOL'] > 1.1:
        return "BUY"
    elif row['Close'] < row['VWAP'] and row['RSI'] < 45 and trend_val == "DOWN" and row['RVOL'] > 1.1:
        return "SELL"
    return None

def scan_stock(s):
    try:
        ticker = s + ".NS"
        df5 = add_indicators(data_5m[ticker].dropna())
        df15 = add_indicators(data_15m[ticker].dropna())
        if len(df5) < 30 or len(df15) < 30: return None
        
        trend_15m = "UP" if df15.iloc[-1]['Close'] > df15.iloc[-1]['EMA20'] else "DOWN"
        last5 = df5.iloc[-1]
        signal = get_signal_logic(last5, trend_15m)
        
        if not signal: return None
        
        sl_val = last5['ATR'] * 1.5
        return {
            "STOCK": s, "SIGNAL": signal, "PRICE": round(last5['Close'],2),
            "RVOL": round(last5['RVOL'],2), "QTY": int(1000/sl_val) if sl_val>0 else 0,
            "SL": round(last5['Close']-sl_val if signal=="BUY" else last5['Close']+sl_val, 2),
            "TGT": round(last5['Close']+(sl_val*2) if signal=="BUY" else last5['Close']-(sl_val*2), 2),
            "TIME": df5.index[-1].strftime('%H:%M')
        }
    except: return None

# =============================
# BACKTEST ENGINE
# =============================
def run_backtest(target_date):
    logs = []
    for s in stocks:
        try:
            ticker = s + ".NS"
            df = add_indicators(data_5m[ticker].dropna())
            df.index = df.index.tz_convert(IST)
            day_data = df[df.index.date == target_date]
            
            if len(day_data) < 20: continue

            for i in range(15, len(day_data) - 10):
                row = day_data.iloc[i]
                trend = "UP" if row['Close'] > row['EMA20'] else "DOWN"
                signal = get_signal_logic(row, trend)
                
                if signal:
                    entry = row['Close']
                    sl = entry - row['ATR']*1.5 if signal=="BUY" else entry + row['ATR']*1.5
                    tgt = entry + row['ATR']*3 if signal=="BUY" else entry - row['ATR']*3
                    
                    # Check outcome in next candles
                    future = day_data.iloc[i+1 : i+30]
                    result = "OPEN"
                    pnl_points = 0
                    
                    for _, f in future.iterrows():
                        if signal == "BUY":
                            if f['Low'] <= sl: result="SL"; pnl_points = sl - entry; break
                            if f['High'] >= tgt: result="TGT"; pnl_points = tgt - entry; break
                        else:
                            if f['High'] >= sl: result="SL"; pnl_points = entry - sl; break
                            if f['Low'] <= tgt: result="TGT"; pnl_points = entry - tgt; break
                    
                    if result != "OPEN":
                        logs.append({"STOCK": s, "SIGNAL": signal, "RESULT": result, "PNL": round(pnl_points, 2)})
                        break # Only one trade per stock per day for clarity
        except: continue
    return pd.DataFrame(logs)

# =============================
# UI TABS
# =============================
tab1, tab2 = st.tabs(["🔴 LIVE PRO SCANNER", "📊 SMART BACKTEST"])

with tab1:
    if st.button("🚀 RUN LIVE SCAN"):
        with ThreadPoolExecutor(max_workers=15) as ex:
            res = [r for r in list(ex.map(scan_stock, stocks)) if r]
        if res:
            df = pd.DataFrame(res)
            st.dataframe(df.style.applymap(lambda x: 'color: #2ecc71' if x=='BUY' else 'color: #e74c3c', subset=['SIGNAL']))
        else: st.warning("No signals.")

with tab2:
    d = st.date_input("Select Date", now.date() - timedelta(days=1))
    if st.button("📈 RUN BACKTEST REPORT"):
        with st.spinner("Calculating..."):
            bt_df = run_backtest(d)
            if not bt_df.empty:
                total = len(bt_df)
                wins = len(bt_df[bt_df['RESULT'] == "TGT"])
                accuracy = (wins/total)*100
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Total Trades", total)
                c2.metric("Win Rate", f"{round(accuracy, 1)}%")
                c3.metric("Net Points", round(bt_df['PNL'].sum(), 2))
                
                st.dataframe(bt_df)
            else: st.info("No trades found for this date.")
