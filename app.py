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
st.set_page_config(page_title="🚀 NSE AI QUANT PRO V7.1 ULTRA", layout="wide")
IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

# UI Styling
st.markdown("""
    <style>
    .nifty-box { padding: 20px; border-radius: 12px; text-align: center; font-size: 24px; font-weight: bold; margin-bottom: 20px; }
    .pos-trend { background-color: #064e3b; color: #10b981; border: 2px solid #10b981; }
    .neg-trend { background-color: #450a0a; color: #f87171; border: 2px solid #f87171; }
    </style>
    """, unsafe_allow_html=True)

# 2. NSE 200 STOCKS LIST
stocks = [
    "ABB", "ACC", "AUBANK", "ADANIENSOL", "ADANIENT", "ADANIPORTS", "AXISBANK", "BAJFINANCE", "BHARTIARTL", 
    "BPCL", "CIPLA", "HDFCBANK", "ICICIBANK", "INFY", "ITC", "LT", "M&M", "RELIANCE", "SBIN", "TCS", 
    "TATAMOTORS", "TITAN", "WIPRO", "ZOMATO", "HAL", "TRENT", "BEL", "NTPC", "ONGC", "POWERGRID"
] # (You can add all 200 stocks here)

# 3. INDICATORS ENGINE
def add_indicators(df):
    df = df.copy()
    if df.empty: return df
    df['Date_Only'] = df.index.date
    df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['PV'] = df['Close'] * df['Volume']
    df['VWAP'] = df.groupby('Date_Only')['PV'].cumsum() / df.groupby('Date_Only')['Volume'].cumsum()
    
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-9))))
    
    # RVOL & ATR
    df['VolAvg'] = df['Volume'].rolling(20).mean()
    df['RVOL'] = df['Volume'] / (df['VolAvg'] + 1e-9)
    df['ATR'] = (df['High'] - df['Low']).rolling(14).mean()
    
    # MACD
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_SIGNAL'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    return df

@st.cache_data(ttl=60)
def fetch_data():
    tickers = [s + ".NS" for s in stocks] + ["^NSEI"]
    d5 = yf.download(tickers, period="6d", interval="15m", group_by="ticker", progress=False)
    d1h = yf.download("^NSEI", period="5d", interval="1h", progress=False)
    return d5, d1h

# 4. SCAN LOGIC (ULTRA)
def scan_stock(s, d5, nifty_5m, n_trend_1h):
    try:
        ticker_data = d5[s + ".NS"].dropna()
        if ticker_data.empty: return []
        df = add_indicators(ticker_data)
        res = []
        
        for i in range(25, len(df)):
            row = df.iloc[i]
            prev = df.iloc[i-1]
            n_row_5m = nifty_5m.reindex(df.index, method='ffill').iloc[i]
            
            # Conditions
            buy_cross = (prev['EMA9'] < prev['VWAP']) and (row['EMA9'] > row['VWAP'])
            sell_cross = (prev['EMA9'] > prev['VWAP']) and (row['EMA9'] < row['VWAP'])
            macd_bull = row['MACD'] > row['MACD_SIGNAL']
            macd_bear = row['MACD'] < row['MACD_SIGNAL']
            
            score = round((row['RVOL'] * 20 + row['RSI']) / 2, 2)
            
            # BUY Logic
            if n_trend_1h == "POSITIVE" and n_row_5m['Close'] > n_row_5m['EMA20']:
                if buy_cross and row['RSI'] > 60 and row['RVOL'] > 1.5 and macd_bull:
                    res.append({"TIME": row.name.astimezone(IST).strftime('%H:%M'), "STOCK": s, "SIGNAL": "BUY", "PRICE": round(row['Close'], 2), "AI_SCORE": score})
            
            # SELL Logic
            elif n_trend_1h == "NEGATIVE" and n_row_5m['Close'] < n_row_5m['EMA20']:
                if sell_cross and row['RSI'] < 40 and row['RVOL'] > 1.5 and macd_bear:
                    res.append({"TIME": row.name.astimezone(IST).strftime('%H:%M'), "STOCK": s, "SIGNAL": "SELL", "PRICE": round(row['Close'], 2), "AI_SCORE": score})
        return res
    except: return []

# 5. UI EXECUTION
d5, d1h = fetch_data()
n_ema_1h = d1h['Close'].ewm(span=20, adjust=False).mean().iloc[-1]
n_trend_1h = "POSITIVE" if d1h['Close'].iloc[-1] > n_ema_1h else "NEGATIVE"
nifty_5m = add_indicators(d5["^NSEI"].dropna())

box_class = "pos-trend" if n_trend_1h == "POSITIVE" else "neg-trend"
st.markdown(f'<div class="nifty-box {box_class}">NIFTY 50 1-HOUR TREND: {n_trend_1h}</div>', unsafe_allow_html=True)

if st.button("🚀 START ULTRA SCAN"):
    with st.spinner("Analyzing NSE 200 Stocks..."):
        with ThreadPoolExecutor(max_workers=30) as executor:
            all_signals = list(executor.map(lambda s: scan_stock(s, d5, nifty_5m, n_trend_1h), stocks))
        
        flat_signals = [item for sublist in all_signals for item in sublist]
        if flat_signals:
            df_res = pd.DataFrame(flat_signals).sort_values(by="AI_SCORE", ascending=False)
            st.dataframe(df_res, use_container_width=True)
            # Excel
            excel_out = io.BytesIO()
            df_res.to_excel(excel_out, index=False)
            st.download_button("📥 Download Excel", excel_out.getvalue(), "V7_ULTRA_Signals.xlsx")
        else: st.info("No strong signals found right now.")
