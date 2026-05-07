import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
from concurrent.futures import ThreadPoolExecutor
import io

# =========================================================
# 1. PAGE CONFIG & STYLING
# =========================================================
st.set_page_config(page_title="🚀 NSE AI QUANT PRO V9.0 SUPREME", layout="wide")
IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.markdown("""
<style>
    .main-title{ text-align:center; font-size:42px; font-weight:bold; color:#22c55e; }
    .sub-title{ text-align:center; font-size:18px; color:#cbd5e1; margin-bottom:25px; }
    .nifty-box { padding: 20px; border-radius: 12px; text-align: center; font-size: 24px; font-weight: bold; margin-bottom: 20px; }
    .pos-trend { background-color: #052e16; color: #22c55e; border: 2px solid #22c55e; }
    .neg-trend { background-color: #450a0a; color: #f87171; border: 2px solid #f87171; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🚀 NSE AI QUANT PRO V9.0 SUPREME</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-title">🕒 LIVE TIME : {now.strftime("%H:%M:%S")} IST</div>', unsafe_allow_html=True)

# =========================================================
# 2. STOCKS LIST & INDICATORS
# =========================================================
stocks = ["ABB","ACC","ADANIENT","ADANIPORTS","AXISBANK","BAJFINANCE","BHARTIARTL","BPCL","CIPLA",
          "HDFCBANK","ICICIBANK","INFY","ITC","LT","M&M","RELIANCE","SBIN","TCS","TATAMOTORS","WIPRO"]

def add_indicators(df):
    df = df.copy()
    if df.empty or len(df) < 50: return pd.DataFrame()
    df['DATE_ONLY'] = df.index.date
    df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['PV'] = df['Close'] * df['Volume']
    df['VWAP'] = df.groupby('DATE_ONLY')['PV'].cumsum() / df.groupby('DATE_ONLY')['Volume'].cumsum()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-9))))
    df['VOLAVG'] = df['Volume'].rolling(20).mean()
    df['RVOL'] = df['Volume'] / (df['VOLAVG'] + 1e-9)
    df['ATR'] = (df['High'] - df['Low']).rolling(14).mean()
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_SIGNAL'] = df['MACD'].ewm(span=9, adjust=False).mean()
    return df

@st.cache_data(ttl=60)
def fetch_data():
    tickers = [s + ".NS" for s in stocks] + ["^NSEI"]
    d15m = yf.download(tickers, period="10d", interval="15m", group_by="ticker", progress=False)
    d1h = yf.download("^NSEI", period="10d", interval="1h", progress=False)
    return d15m, d1h

# =========================================================
# 3. SCAN ENGINE (Completing your code)
# =========================================================
def scan_single_stock(stock, data_15m, nifty_15m, market_trend):
    try:
        ticker = stock + ".NS"
        df = add_indicators(data_15m[ticker].dropna())
        if df.empty: return []
        
        results = []
        today_date = now.date()
        df_today = df[df.index.date == today_date]
        
        for i in range(len(df_today)):
            idx = df.index.get_loc(df_today.index[i])
            row = df.iloc[idx]
            prev = df.iloc[idx-1]
            n_row = nifty_15m.reindex(df.index, method='ffill').iloc[idx]
            
            # EMA9-VWAP Cross
            buy_cross = (prev['EMA9'] < prev['VWAP']) and (row['EMA9'] > row['VWAP'])
            sell_cross = (prev['EMA9'] > prev['VWAP']) and (row['EMA9'] < row['VWAP'])
            
            # SUPREME CONDITIONS
            if market_trend == "POSITIVE" and n_row['Close'] > n_row['EMA20']:
                if (buy_cross or row['EMA9'] > row['VWAP']) and row['RSI'] > 55 and row['MACD'] > row['MACD_SIGNAL']:
                    results.append({"TIME": row.name.astimezone(IST).strftime('%H:%M'), "STOCK": stock, "SIGNAL": "BUY", "PRICE": round(row['Close'], 2), "RVOL": round(row['RVOL'], 2), "ATR": round(row['ATR'], 2)})
            
            elif market_trend == "NEGATIVE" and n_row['Close'] < n_row['EMA20']:
                if (sell_cross or row['EMA9'] < row['VWAP']) and row['RSI'] < 45 and row['MACD'] < row['MACD_SIGNAL']:
                    results.append({"TIME": row.name.astimezone(IST).strftime('%H:%M'), "STOCK": stock, "SIGNAL": "SELL", "PRICE": round(row['Close'], 2), "RVOL": round(row['RVOL'], 2), "ATR": round(row['ATR'], 2)})
        return results
    except: return []

# =========================================================
# 4. UI EXECUTION
# =========================================================
d15m, d1h = fetch_data()
nifty_15m = add_indicators(d15m["^NSEI"].dropna())
n_last_1h = d1h['Close'].iloc[-1]
n_ema_1h = d1h['Close'].ewm(span=20, adjust=False).mean().iloc[-1]
market_trend = "POSITIVE" if n_last_1h > n_ema_1h else "NEGATIVE"

# Top Trend Box
box_class = "pos-trend" if market_trend == "POSITIVE" else "neg-trend"
st.markdown(f'<div class="nifty-box {box_class}">NIFTY 50 1-HOUR TREND: {market_trend} {"📈" if market_trend == "POSITIVE" else "📉"}</div>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🔍 SUPREME TRACKER", "📊 BACKTEST REPORT"])

with tab1:
    if st.button("🚀 RUN SUPREME SCAN"):
        with ThreadPoolExecutor(max_workers=20) as executor:
            all_res = list(executor.map(lambda s: scan_single_stock(s, d15m, nifty_15m, market_trend), stocks))
        flat_res = [item for sublist in all_res for item in sublist]
        if flat_res:
            df_final = pd.DataFrame(flat_res).sort_values(by="TIME", ascending=False)
            st.dataframe(df_final, use_container_width=True)
            # Excel Download
            out = io.BytesIO()
            df_final.to_excel(out, index=False)
            st.download_button("📥 Download Supreme Report", out.getvalue(), "Supreme_Signals.xlsx")
        else: st.info("No supreme signals found for current trend.")

with tab2:
    st.write("Backtest results will appear here based on 10-day history.")
