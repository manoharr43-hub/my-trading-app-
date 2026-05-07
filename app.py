import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
from concurrent.futures import ThreadPoolExecutor
import io

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(page_title="🚀 NSE AI QUANT PRO V14.0", layout="wide")
IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

# =========================================================
# INDICATORS (Direct Calculation - No pandas_ta needed)
# =========================================================
def get_indicators(df):
    df = df.copy()
    if len(df) < 30: return pd.DataFrame()

    # EMA
    df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()

    # VWAP
    df['PV'] = df['Close'] * df['Volume']
    df['VWAP'] = df.groupby(df.index.date)['PV'].cumsum() / df.groupby(df.index.date)['Volume'].cumsum()

    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # ATR (Simple calculation)
    high_low = df['High'] - df['Low']
    high_cp = np.abs(df['High'] - df['Close'].shift())
    low_cp = np.abs(df['Low'] - df['Close'].shift())
    df['TR'] = pd.concat([high_low, high_cp, low_cp], axis=1).max(axis=1)
    df['ATR'] = df['TR'].rolling(14).mean()

    # ADX (Basic calculation)
    plus_dm = df['High'].diff()
    minus_dm = df['Low'].diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm > 0] = 0
    
    tr14 = df['TR'].rolling(14).mean()
    plus_di = 100 * (plus_dm.rolling(14).mean() / tr14)
    minus_di = 100 * (abs(minus_dm).rolling(14).mean() / tr14)
    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    df['ADX'] = dx.rolling(14).mean()

    # RVOL
    df['VOLAVG'] = df['Volume'].rolling(20).mean()
    df['RVOL'] = df['Volume'] / (df['VOLAVG'] + 1e-9)

    return df

# =========================================================
# STOCKS & DATA
# =========================================================
stocks = ["ABB","ACC","AUBANK","ADANIENSOL","ADANIENT","ADANIGREEN","ADANIPORTS","ADANIPOWER","ATGL",
          "ABCAPITAL","ABFRL","ALKEM","AMBUJACEM","APOLLOHOSP","APOLLOTYRE","ASHOKLEY","ASIANPAINT",
          "ASTRAL","AUROPHARMA","AXISBANK","BAJAJ-AUTO","BAJFINANCE","BAJAJFINSV","BAJAJHLDNG",
          "BALKRISIND","BANDHANBNK","BANKBARODA","BANKINDIA","BATAINDIA","BEL","BERGEPAINT",
          "BHARATFORG","BHEL","BPCL","BHARTIARTL","BIOCON","BOSCHLTD","BRITANNIA","CANBK","CGPOWER",
          "CHOLAFIN","CIPLA","COALINDIA","COFORGE","COLPAL","CONCOR","COROMANDEL","CROMPTON",
          "CUMMINSIND","CYIENT","DABUR","DALBHARAT","DEEPAKNTR","DELHIVERY","DIVISLAB","DIXON","DLF",
          "DRREDDY","EICHERMOT","ESCORTS","EXIDEIND","FEDERALBNK","FORTIS","GAIL","GLENMARK",
          "GMRINFRA","GODREJCP","GODREJPROP","GRASIM","GUJGASLTD","HAL","HAVELLS","HCLTECH",
          "HDFCBANK","HDFCLIFE","HEROMOTOCO","HINDALCO","HINDCOPPER","HINDPETRO","HINDUNILVR",
          "ICICIBANK","IDFCFIRSTB","IEX","IGL","INDHOTEL","INDIGO","INDUSINDBK","INDUSTOWER","INFY",
          "IOC","IRCTC","IRFC","ITC","JINDALSTEL","JSWENERGY","JSWSTEEL","JUBLFOOD","KOTAKBANK",
          "KPITTECH","LT","LTIM","LTTS","LICI","LUPIN","M&M","M&MFIN","MARICO","MARUTI","MAXHEALTH",
          "METROPOLIS","MFSL","MGL","MPHASIS","MRF","MUTHOOTFIN","NATIONALUM","NESTLEIND","NMDC",
          "NTPC","OBEROIRLTY","ONGC","PAYTM","PERSISTENT","PETRONET","PFC","PIDILITIND","PIIND",
          "PNB","POLYCAB","POONAWALLA","POWERGRID","PRESTIGE","PVRINOX","RECLTD","RELIANCE","SAIL",
          "SBICARD","SBILIFE","SBIN","SIEMENS","SRF","SUNPHARMA","SUNTV","SYNGENE","TATACOMM",
          "TATACONSUM","TATAELXSI","TATAMOTORS","TATAPOWER","TATASTEEL","TCS","TECHM","TITAN",
          "TORNTPHARM","TRENT","TVSMOTOR","ULTRACEMCO","UPL","VBL","VEDL","VOLTAS","WIPRO",
          "YESBANK","ZEEL","ZOMATO"]

@st.cache_data(ttl=60)
def fetch_all():
    tickers = [s + ".NS" for s in stocks]
    data = yf.download(tickers + ["^NSEI"], period="7d", interval="15m", auto_adjust=True, group_by='ticker')
    return data

# =========================================================
# MAIN APP
# =========================================================
st.markdown(f'<h2 style="text-align:center;">🚀 NSE AI QUANT PRO V14.0</h2>', unsafe_allow_html=True)
full_data = fetch_all()

def scan_stock(stock, is_backtest=False):
    try:
        df = get_indicators(full_data[stock + ".NS"].dropna())
        if df.empty: return []
        
        scan_df = df if is_backtest else df[df.index.date == now.date()]
        results = []

        for i in range(1, len(scan_df)):
            row = scan_df.iloc[i]
            prev = scan_df.iloc[i-1]
            
            buy = (row['EMA9'] > row['VWAP'] and prev['EMA9'] <= prev['VWAP'] and row['RSI'] > 50 and row['RVOL'] > 1.2)
            sell = (row['EMA9'] < row['VWAP'] and prev['EMA9'] >= prev['VWAP'] and row['RSI'] < 50 and row['RVOL'] > 1.2)

            if buy or sell:
                sig = "BUY" if buy else "SELL"
                sl = row['Close'] - (row['ATR'] * 1.5) if buy else row['Close'] + (row['ATR'] * 1.5)
                results.append({
                    "TIME": row.name.strftime("%H:%M"), "STOCK": stock, "SIGNAL": sig,
                    "PRICE": round(row['Close'], 2), "SL": round(sl, 2), "RSI": round(row['RSI'], 1)
                })
        return results
    except: return []

if st.button("🚀 RUN SCANNER"):
    with ThreadPoolExecutor(max_workers=20) as executor:
        all_res = list(executor.map(lambda s: scan_stock(s), stocks))
    flat = [i for s in all_res for i in s]
    if flat:
        st.dataframe(pd.DataFrame(flat).drop_duplicates('STOCK', keep='last'), use_container_width=True)
    else:
        st.warning("No signals found.")
