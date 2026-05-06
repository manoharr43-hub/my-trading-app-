import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from concurrent.futures import ThreadPoolExecutor
import io

# =============================
# CONFIG & UI THEME
# =============================
st.set_page_config(page_title="🚀 NSE AI PRO V100 FINAL PRO", layout="wide")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

# Custom Styling
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1f2937; padding: 15px; border-radius: 10px; border: 1px solid #374151; }
    div[data-testid="stExpander"] { border: 1px solid #374151; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 NSE AI PRO V100 - QUANT PRO SYSTEM")
st.subheader(f"📅 {now.strftime('%d-%b-%Y')} | {now.strftime('%H:%M:%S')} IST")

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
    
    # EMA 20
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    
    # VWAP
    df['Date'] = df.index.date
    df['PV'] = df['Close'] * df['Volume']
    df['VWAP'] = df.groupby('Date')['PV'].cumsum() / df.groupby('Date')['Volume'].cumsum()
    
    # ATR (14)
    tr = pd.concat([df['High']-df['Low'], abs(df['High']-df['Close'].shift()), abs(df['Low']-df['Close'].shift())], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()
    
    # RSI (14)
    delta = df['Close'].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-9))))
    
    # RVOL (Relative Volume)
    df['VolAvg'] = df['Volume'].rolling(20).mean()
    df['RVOL'] = df['Volume'] / (df['VolAvg'] + 1e-9)
    
    return df

# =============================
# DATA FETCHING
# =============================
@st.cache_data(ttl=60)
def fetch_all_data(interval):
    tickers = [s + ".NS" for s in stocks] + ["^NSEI"]
    return yf.download(tickers, period="5d", interval=interval, group_by="ticker", progress=False)

data_5m = fetch_all_data("5m")
data_15m = fetch_all_data("15m")

# =============================
# SIGNAL LOGIC
# =============================
def get_signal_logic(row, trend_val):
    # Rule: Price > VWAP, RSI > 55, Trend UP, High Volume
    if row['Close'] > row['VWAP'] and row['RSI'] > 55 and trend_val == "UP" and row['RVOL'] > 1.1:
        return "BUY"
    # Rule: Price < VWAP, RSI < 45, Trend DOWN, High Volume
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
        
        # Position Sizing (Risk: ₹1000)
        risk_amount = 1000
        sl_points = last5['ATR'] * 1.5
        entry = last5['Close']
        sl = entry - sl_points if signal == "BUY" else entry + sl_points
        tgt = entry + (sl_points * 2.5) if signal == "BUY" else entry - (sl_points * 2.5)
        
        qty = int(risk_amount / sl_points) if sl_points > 0 else 0

        return {
            "STOCK": s,
            "SIGNAL": signal,
            "PRICE": round(entry, 2),
            "RVOL": round(last5['RVOL'], 2),
            "RSI": round(last5['RSI'], 1),
            "QTY": qty,
            "SL": round(sl, 2),
            "TGT": round(tgt, 2),
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
            day_df = df[df.index.date == target_date]
            
            if len(day_df) < 20: continue

            for i in range(15, len(day_df) - 10):
                row = day_df.iloc[i]
                trend = "UP" if row['Close'] > row['EMA20'] else "DOWN"
                signal = get_signal_logic(row, trend)
                
                if signal:
                    entry = row['Close']
                    sl = entry - row['ATR']*1.5 if signal=="BUY" else entry + row['ATR']*1.5
                    tgt = entry + row['ATR']*3 if signal=="BUY" else entry - row['ATR']*3
                    
                    future = day_df.iloc[i+1 : i+35] # Look ahead
                    result = "OPEN"
                    pnl = 0
                    
                    for _, f in future.iterrows():
                        if signal == "BUY":
                            if f['Low'] <= sl: result="SL"; pnl = sl-entry; break
                            if f['High'] >= tgt: result="TGT"; pnl = tgt-entry; break
                        else:
                            if f['High'] >= sl: result="SL"; pnl = entry-sl; break
                            if f['Low'] <= tgt: result="TGT"; pnl = entry-tgt; break
                    
                    if result != "OPEN":
                        logs.append({"STOCK": s, "SIGNAL": signal, "RESULT": result, "PNL_PTS": round(pnl, 2)})
                        break 
        except: continue
    return pd.DataFrame(logs)

# =============================
# MAIN UI
# =============================
tab1, tab2 = st.tabs(["🔴 LIVE PRO SCANNER", "📊 SMART BACKTEST"])

with tab1:
    # Market Overview
    try:
        n_df = data_5m["^NSEI"].dropna()
        n_last = n_df.iloc[-1]['Close']
        n_prev = n_df.iloc[-2]['Close']
        n_chg = ((n_last - n_prev)/n_prev)*100
        st.metric("NIFTY 50", f"{round(n_last,2)}", f"{round(n_chg,2)}%")
    except: st.info("Nifty status pending...")

    if st.button("🚀 START SCANNING"):
        with st.spinner("Analyzing Market..."):
            with ThreadPoolExecutor(max_workers=15) as executor:
                res = [r for r in list(executor.map(scan_stock, stocks)) if r]
            
            if res:
                df_res = pd.DataFrame(res)
                
                m1, m2, m3 = st.columns(3)
                m1.metric("Signals Found", len(df_res))
                m2.metric("Buys", len(df_res[df_res['SIGNAL']=='BUY']))
                m3.metric("Sells", len(df_res[df_res['SIGNAL']=='SELL']))
                
                # FIXED: Using .map instead of .applymap for Pandas 2.0+
                st.dataframe(df_res.style.map(
                    lambda x: 'background-color: #1e4620; color: #2ecc71' if x == 'BUY' else 'background-color: #4c1e1e; color: #e74c3c',
                    subset=['SIGNAL']
                ), use_container_width=True)
            else:
                st.info("No high-probability signals found.")

with tab2:
    d_input = st.date_input("Backtest Date", now.date() - timedelta(days=1))
    if st.button("📈 RUN REPORT"):
        with st.spinner("Crunching data..."):
            bt_results = run_backtest(d_input)
            if not bt_results.empty:
                t_trades = len(bt_results)
                t_wins = len(bt_results[bt_results['RESULT'] == "TGT"])
                acc = (t_wins/t_trades)*100
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Total Trades", t_trades)
                c2.metric("Accuracy", f"{round(acc, 1)}%")
                c3.metric("Points PnL", round(bt_results['PNL_PTS'].sum(), 2))
                
                st.dataframe(bt_results, use_container_width=True)
            else:
                st.warning("No trades found for this criteria on selected date.")
