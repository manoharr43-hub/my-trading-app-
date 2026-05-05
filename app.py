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
st.set_page_config(page_title="🚀 NSE AI PRO V46.0", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V46.0 - SMART SCANNER")
st.write(f"🕒 **Market Time:** {now.strftime('%Y-%m-%d %H:%M:%S')}")

# =============================
# NSE 200 COMPLETE STOCK LIST
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
# CORE INDICATORS LOGIC
# =============================
def add_indicators(df):
    df = df.copy()
    if len(df) < 30: return df
    
    # EMA 20
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    
    # VWAP
    df['Date_Only'] = df.index.date
    df['PV'] = df['Close'] * df['Volume']
    df['VWAP'] = df.groupby('Date_Only')['PV'].cumsum() / df.groupby('Date_Only')['Volume'].cumsum()
    
    # ATR (14)
    high_low = df['High'] - df['Low']
    tr = pd.concat([high_low, abs(df['High'] - df['Close'].shift()), abs(df['Low'] - df['Close'].shift())], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()
    
    # RSI (14)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Volume Avg
    df['VolAvg'] = df['Volume'].rolling(20).mean()
    
    return df

@st.cache_data(ttl=60)
def fetch_data(symbols, interval, period):
    tickers = [s + ".NS" for s in symbols]
    return yf.download(tickers, period=period, interval=interval, group_by='ticker', progress=False)

# Nifty 50 Trend Check
def get_nifty_status():
    try:
        nifty = yf.download("^NSEI", period="2d", interval="5m", progress=False)
        change = ((nifty['Close'].iloc[-1] - nifty['Close'].iloc[0]) / nifty['Close'].iloc[0]) * 100
        return round(float(change), 2)
    except: return 0.0

# =============================
# MAIN EXECUTION
# =============================
nifty_pc = get_nifty_status()
nifty_color = "green" if nifty_pc >= 0 else "red"
st.markdown(f"### Market Trend (Nifty 50): <span style='color:{nifty_color}'>{nifty_pc}%</span>", unsafe_allow_html=True)

with st.spinner("🚀 Scanning NSE 200 Stocks..."):
    data_5m = fetch_data(stocks, "5m", "5d")

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Report')
    return output.getvalue()

tab1, tab2 = st.tabs(["🔍 LIVE SCANNER", "📊 BACKTEST"])

with tab1:
    if st.button("RUN LIVE SCAN"):
        results = []
        for s in stocks:
            try:
                ticker = s + ".NS"
                if ticker not in data_5m.columns.levels[0]: continue
                df_raw = data_5m[ticker].dropna()
                if len(df_raw) < 20: continue
                
                df = add_indicators(df_raw)
                l = df.iloc[-1]
                
                dist = abs(l['Close'] - l['EMA20']) / l['EMA20']
                
                if dist < 0.004:
                    signal = "None"
                    # Buy: Price > VWAP + RSI > 50
                    if l['Close'] > l['VWAP'] and l['Close'] > l['Open'] and l['RSI'] > 50:
                        signal = "BUY 🟢"
                    # Sell: Price < VWAP + RSI < 50
                    elif l['Close'] < l['VWAP'] and l['Close'] < l['Open'] and l['RSI'] < 50:
                        signal = "SELL 🔴"
                    
                    if signal != "None":
                        entry = round(l['Close'], 2)
                        results.append({
                            "TIME": df.index[-1].astimezone(IST).strftime('%H:%M'),
                            "STOCK": s, "ACTION": signal, "RSI": round(l['RSI'],1),
                            "VOL": "🔥" if l['Volume'] > l['VolAvg']*2.5 else "Norm",
                            "PRICE": entry,
                            "SL": round(entry - (l['ATR']*1.5) if "BUY" in signal else entry + (l['ATR']*1.5), 2),
                            "TGT": round(entry + (l['ATR']*3) if "BUY" in signal else entry - (l['ATR']*3), 2)
                        })
            except Exception: continue
        
        if results:
            df_res = pd.DataFrame(results)
            st.table(df_res) # Table used for cleaner UI
            st.download_button("📥 Excel", data=to_excel(df_res), file_name="Live_Scan.xlsx")
        else:
            st.info("No pullback signals found.")

with tab2:
    bt_date = st.date_input("History Date", value=now.date() - timedelta(days=1))
    if st.button("RUN BACKTEST"):
        bt_logs = []
        for s in stocks:
            try:
                ticker = s + ".NS"
                if ticker not in data_5m.columns.levels[0]: continue
                df_raw = data_5m[ticker].dropna()
                df_raw.index = df_raw.index.tz_convert(IST)
                df_day = add_indicators(df_raw)
                df_day = df_day[df_day.index.date == bt_date]
                
                if df_day.empty: continue
                last_time = None

                for i in range(15, len(df_day)):
                    row = df_day.iloc[i]
                    if last_time and (df_day.index[i] - last_time) < timedelta(minutes=45): continue
                        
                    dist = abs(row['Close'] - row['EMA20']) / row['EMA20']
                    if dist < 0.004:
                        sig = "None"
                        if row['Close'] > row['VWAP'] and row['RSI'] > 50: sig = "BUY 🟢"
                        elif row['Close'] < row['VWAP'] and row['RSI'] < 50: sig = "SELL 🔴"
                        
                        if sig != "None":
                            entry = row['Close']
                            sl = entry - (row['ATR']*1.5) if "BUY" in sig else entry + (row['ATR']*1.5)
                            tgt = entry + (row['ATR']*3) if "BUY" in sig else entry - (row['ATR']*3)
                            
                            outcome = "OPEN"
                            future = df_day.iloc[i+1 : i+30]
                            for _, f in future.iterrows():
                                if "BUY" in sig:
                                    if f['High'] >= tgt: outcome = "🎯 TGT"; break
                                    if f['Low'] <= sl: outcome = "🛑 SL"; break
                                else:
                                    if f['Low'] <= tgt: outcome = "🎯 TGT"; break
                                    if f['High'] >= sl: outcome = "🛑 SL"; break

                            bt_logs.append({
                                "TIME": df_day.index[i].strftime('%H:%M'),
                                "STOCK": s, "TYPE": sig, "RESULT": outcome
                            })
                            last_time = df_day.index[i]
            except: continue
        
        if bt_logs:
            st.dataframe(pd.DataFrame(bt_logs), use_container_width=True)
        else:
            st.warning("No signals found.")
