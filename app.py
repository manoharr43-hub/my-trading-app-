import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
from concurrent.futures import ThreadPoolExecutor
import io

# ==========================================
# 1. CONFIG & TIMEZONE SETUP
# ==========================================
st.set_page_config(page_title="🚀 NSE AI QUANT PRO V6.8", layout="wide")
IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

# UI Styling for Top Box
st.markdown("""
    <style>
    .nifty-box { padding: 25px; border-radius: 12px; text-align: center; font-size: 24px; font-weight: bold; margin-bottom: 20px; }
    .pos-trend { background-color: #064e3b; color: #10b981; border: 2px solid #10b981; }
    .neg-trend { background-color: #450a0a; color: #f87171; border: 2px solid #f87171; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. COMPLETE NSE 200 STOCKS LIST
# ==========================================
stocks = [
    "ABB", "ACC", "AUBANK", "ADANIENSOL", "ADANIENT", "ADANIGREEN", "ADANIPORTS", "ADANIPOWER", "ATGL", "ABCAPITAL", 
    "ABFRL", "ALKEM", "AMBUJACEM", "APOLLOHOSP", "APOLLOTYRE", "ASHOKLEY", "ASIANPAINT", "ASTRAL", "AUROPHARMA", 
    "AXISBANK", "BAJAJ-AUTO", "BAJFINANCE", "BAJAJFINSV", "BAJAJHLDNG", "BALKRISIND", "BANDHANBNK", "BANKBARODA", 
    "BANKINDIA", "BATAINDIA", "BEL", "BERGEPAINT", "BHARATFORG", "BHEL", "BPCL", "BHARTIARTL", "BIOCON", 
    "BOSCHLTD", "BRITANNIA", "CANBK", "CGPOWER", "CHOLAFIN", "CIPLA", "COALINDIA", "COFORGE", "COLPAL", 
    "CONCOR", "COROMANDEL", "CROMPTON", "CUMMINSIND", "CYIENT", "DABUR", "DALBHARAT", "DEEPAKNTR", "DELHIVERY", 
    "DIVISLAB", "DIXON", "DLF", "DRREDDY", "EICHERMOT", "ESCORTS", "EXIDEIND", "FEDERALBNK", "FORTIS", "GAIL", 
    "GLENMARK", "GMRINFRA", "GODREJCP", "GODREJPROP", "GRASIM", "GUJGASLTD", "HAL", "HAVELLS", "HCLTECH", 
    "HDFCBANK", "HDFCLIFE", "HEROMOTOCO", "HINDALCO", "HINDCOPPER", "HINDPETRO", "HINDUNILVR", "ICICIBANK", 
    "IDFCFIRSTB", "IEX", "IGL", "INDHOTEL", "INDIGO", "INDUSINDBK", "INDUSTOWER", "INFY", "IOC", "IRCTC", 
    "IRFC", "ITC", "JINDALSTEL", "JSWENERGY", "JSWSTEEL", "JUBLFOOD", "KOTAKBANK", "KPITTECH", "LT", "LTIM", 
    "LTTS", "LICI", "LUPIN", "M&M", "M&MFIN", "MARICO", "MARUTI", "MAXHEALTH", "METROPOLIS", "MFSL", "MGL", 
    "MPHASIS", "MRF", "MUTHOOTFIN", "NATIONALUM", "NESTLEIND", "NMDC", "NTPC", "OBEROIRLTY", "ONGC", "PAYTM", 
    "PERSISTENT", "PETRONET", "PFC", "PIDILITIND", "PIIND", "PNB", "POLYCAB", "POONAWALLA", "POWERGRID", 
    "PRESTIGE", "PVRINOX", "RECLTD", "RELIANCE", "SAIL", "SBICARD", "SBILIFE", "SBIN", "SIEMENS", "SRF", 
    "SUNPHARMA", "SUNTV", "SYNGENE", "TATACOMM", "TATACONSUM", "TATAELXSI", "TATAMOTORS", "TATAPOWER", 
    "TATASTEEL", "TCS", "TECHM", "TITAN", "TORNTPHARM", "TRENT", "TVSMOTOR", "ULTRACEMCO", "UPL", "VBL", 
    "VEDL", "VOLTAS", "WIPRO", "YESBANK", "ZEEL", "ZOMATO"
]

# 3. INDICATORS ENGINE
def add_indicators(df):
    df = df.copy()
    if df.empty: return df
    df['Date_Only'] = df.index.date
    df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['PV'] = df['Close'] * df['Volume']
    df['VWAP'] = df.groupby('Date_Only')['PV'].cumsum() / df.groupby('Date_Only')['Volume'].cumsum()
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-9))))
    
    tr = pd.concat([df['High']-df['Low'], (df['High']-df['Close'].shift()).abs(), (df['Low']-df['Close'].shift()).abs()], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()
    df['VolAvg'] = df['Volume'].rolling(20).mean()
    df['RVOL'] = df['Volume'] / (df['VolAvg'] + 1e-9)
    df['Range_Width'] = (df['High'].rolling(15).max() - df['Low'].rolling(15).min()) / df['Low'].rolling(15).min() * 100
    return df

@st.cache_data(ttl=60)
def fetch_data():
    tickers = [s + ".NS" for s in stocks] + ["^NSEI"]
    d5 = yf.download(tickers, period="6d", interval="5m", group_by="ticker", progress=False)
    d1h = yf.download("^NSEI", period="5d", interval="1h", progress=False)
    return d5, d1h

# 4. SCAN LOGIC
def scan_stock(s, d5, n_5m, n_trend_1h):
    try:
        df = add_indicators(d5[s + ".NS"].dropna())
        res = []
        for i in range(25, len(df)):
            row = df.iloc[i]
            prev = df.iloc[i-1]
            n_row_5m = n_5m.reindex(df.index, method='ffill').iloc[i]
            
            ema_dist = (row['Close'] - row['EMA20']) / row['EMA20'] * 100
            is_healthy = abs(ema_dist) < 0.85 and (row['High'] - row['Low']) < (row['ATR'] * 1.9)

            if n_trend_1h == "POSITIVE" and n_row_5m['Close'] > n_row_5m['EMA20']:
                if row['Close'] > row['VWAP'] and row['EMA9'] > row['EMA21'] and row['RSI'] > 50 and is_healthy:
                    if (prev['Range_Width'] < 0.45 and row['Close'] > prev['High']) or row['RVOL'] > 2.2:
                        res.append({"TIME": row.name.astimezone(IST).strftime('%H:%M'), "STOCK": s, "SIGNAL": "BUY", "PRICE": round(row['Close'], 2), "RVOL": round(row['RVOL'], 2)})

            elif n_trend_1h == "NEGATIVE" and n_row_5m['Close'] < n_row_5m['EMA20']:
                if row['Close'] < row['VWAP'] and row['EMA9'] < row['EMA21'] and row['RSI'] < 45 and is_healthy:
                    if (prev['Range_Width'] < 0.45 and row['Close'] < prev['Low']) or row['RVOL'] > 2.2:
                        res.append({"TIME": row.name.astimezone(IST).strftime('%H:%M'), "STOCK": s, "SIGNAL": "SELL", "PRICE": round(row['Close'], 2), "RVOL": round(row['RVOL'], 2)})
        return res
    except: return []

# 5. UI EXECUTION
d5, d1h = fetch_data()
nifty_5m = add_indicators(d5["^NSEI"].dropna())
n_trend_1h = "POSITIVE" if d1h['Close'].iloc[-1] > d1h['Close'].ewm(span=20).mean().iloc[-1] else "NEGATIVE"

box_class = "pos-trend" if n_trend_1h == "POSITIVE" else "neg-trend"
st.markdown(f'<div class="nifty-box {box_class}">NIFTY 50 1-HOUR TREND: {n_trend_1h} {"📈" if n_trend_1h == "POSITIVE" else "📉"}</div>', unsafe_allow_html=True)

if st.button("🚀 START FULL SCAN (NSE 200)"):
    with st.spinner("Analyzing 200 stocks..."):
        with ThreadPoolExecutor(max_workers=25) as executor:
            all_signals = list(executor.map(lambda s: scan_stock(s, d5, nifty_5m, n_trend_1h), stocks))
        
        flat_signals = [item for sublist in all_signals for item in sublist]
        if flat_signals:
            df_res = pd.DataFrame(flat_signals).sort_values(by="TIME", ascending=False)
            st.dataframe(df_res, use_container_width=True)
            
            # Excel Download
            excel_out = io.BytesIO()
            with pd.ExcelWriter(excel_out, engine='xlsxwriter') as writer:
                df_res.to_excel(writer, index=False, sheet_name='Today_Signals')
            st.download_button("📥 Download Excel Report", excel_out.getvalue(), f"NSE200_Signals_{now.strftime('%d%m')}.xlsx")
        else:
            st.info("No high-probability signals found for the current trend.")
