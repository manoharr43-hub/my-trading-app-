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
st.set_page_config(page_title="🚀 NSE AI QUANT PRO V7.2 ULTRA", layout="wide")
IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

# UI Styling
st.markdown("""
    <style>
    .nifty-box { padding: 25px; border-radius: 12px; text-align: center; font-size: 24px; font-weight: bold; margin-bottom: 20px; }
    .pos-trend { background-color: #064e3b; color: #10b981; border: 2px solid #10b981; }
    .neg-trend { background-color: #450a0a; color: #f87171; border: 2px solid #f87171; }
    </style>
    """, unsafe_allow_html=True)

# 2. FULL NSE 200 LIST
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
    if df.empty or len(df) < 30: return pd.DataFrame()
    df['Date_Only'] = df.index.date
    df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['PV'] = df['Close'] * df['Volume']
    df['VWAP'] = df.groupby('Date_Only')['PV'].cumsum() / df.groupby('Date_Only')['Volume'].cumsum()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-9))))
    df['VolAvg'] = df['Volume'].rolling(20).mean()
    df['RVOL'] = df['Volume'] / (df['VolAvg'] + 1e-9)
    df['ATR'] = (df['High'] - df['Low']).rolling(14).mean()
    return df

@st.cache_data(ttl=60)
def fetch_data():
    tickers = [s + ".NS" for s in stocks] + ["^NSEI"]
    d5 = yf.download(tickers, period="6d", interval="15m", group_by="ticker", progress=False)
    d1h = yf.download("^NSEI", period="5d", interval="1h", progress=False)
    return d5, d1h

# 4. CORE SCAN LOGIC
def scan_stock(s, d5, nifty_5m, n_trend_1h, is_backtest=False):
    try:
        ticker_data = d5[s + ".NS"].dropna()
        df = add_indicators(ticker_data)
        if df.empty: return []
        
        res = []
        today_date = now.date()
        scan_df = df if is_backtest else df[df.index.date == today_date]
        
        for i in range(len(scan_df)):
            idx = df.index.get_loc(scan_df.index[i])
            if idx < 1: continue
            
            row = df.iloc[idx]
            prev = df.iloc[idx-1]
            n_row_5m = nifty_5m.reindex(df.index, method='ffill').iloc[idx]
            
            cross_up = (prev['EMA9'] < prev['VWAP']) and (row['EMA9'] > row['VWAP'])
            cross_down = (prev['EMA9'] > prev['VWAP']) and (row['EMA9'] < row['VWAP'])
            score = round((row['RVOL'] * 20 + row['RSI']) / 2, 2)

            if n_trend_1h == "POSITIVE" and n_row_5m['Close'] > n_row_5m['EMA20']:
                if (cross_up or row['EMA9'] > row['VWAP']) and row['RSI'] > 55 and row['RVOL'] > 1.3:
                    res.append({"DATE": row.name.strftime('%d-%b'), "TIME": row.name.strftime('%H:%M'), "STOCK": s, "SIGNAL": "BUY", "PRICE": round(row['Close'], 2), "AI_SCORE": score, "ATR": row['ATR']})
            elif n_trend_1h == "NEGATIVE" and n_row_5m['Close'] < n_row_5m['EMA20']:
                if (cross_down or row['EMA9'] < row['VWAP']) and row['RSI'] < 45 and row['RVOL'] > 1.3:
                    res.append({"DATE": row.name.strftime('%d-%b'), "TIME": row.name.strftime('%H:%M'), "STOCK": s, "SIGNAL": "SELL", "PRICE": round(row['Close'], 2), "AI_SCORE": score, "ATR": row['ATR']})
        return res
    except: return []

# 5. UI EXECUTION
d5, d1h = fetch_data()
nifty_5m = add_indicators(d5["^NSEI"].dropna())
n_trend_1h = "POSITIVE" if d1h['Close'].iloc[-1] > d1h['Close'].ewm(span=20).mean().iloc[-1] else "NEGATIVE"

box_class = "pos-trend" if n_trend_1h == "POSITIVE" else "neg-trend"
st.markdown(f'<div class="nifty-box {box_class}">NIFTY 50 1-HOUR TREND: {n_trend_1h}</div>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🔍 LIVE TRACKER (Today)", "📊 5-DAY BACKTEST"])

with tab1:
    if st.button("🚀 START LIVE SCAN"):
        with st.spinner("Scanning 200 stocks..."):
            with ThreadPoolExecutor(max_workers=30) as executor:
                all_res = list(executor.map(lambda s: scan_stock(s, d5, nifty_5m, n_trend_1h), stocks))
            flat_res = [item for sublist in all_res for item in sublist]
            if flat_res:
                df_live = pd.DataFrame(flat_res).sort_values(by="TIME", ascending=False)
                st.dataframe(df_live.drop(columns=['DATE', 'ATR']), use_container_width=True)
                excel_out = io.BytesIO()
                df_live.to_excel(excel_out, index=False)
                st.download_button("📥 Download Excel", excel_out.getvalue(), "Today_Signals.xlsx")
            else: st.info("No signals found.")

with tab2:
    if st.button("📊 RUN BACKTEST"):
        with st.spinner("Running Backtest..."):
            with ThreadPoolExecutor(max_workers=30) as executor:
                all_bt = list(executor.map(lambda s: scan_stock(s, d5, nifty_5m, n_trend_1h, is_backtest=True), stocks))
            flat_bt = [item for sublist in all_bt for item in sublist]
            if flat_bt:
                df_bt = pd.DataFrame(flat_bt)
                st.dataframe(df_bt, use_container_width=True)
                bt_out = io.BytesIO()
                df_bt.to_excel(bt_out, index=False)
                st.download_button("📥 Download Backtest Excel", bt_out.getvalue(), "Backtest_Report.xlsx")
