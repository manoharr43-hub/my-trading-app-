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
st.set_page_config(page_title="🚀 NSE AI QUANT PRO V9.3 SUPREME", layout="wide")
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

st.markdown('<div class="main-title">🚀 NSE AI QUANT PRO V9.3 SUPREME</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-title">🕒 LIVE TIME : {now.strftime("%H:%M:%S")} IST</div>', unsafe_allow_html=True)

# =========================================================
# 2. NSE 200 STOCKS LIST
# =========================================================
stocks = [
    "ABB", "ACC", "AUBANK", "ADANIENSOL", "ADANIENT", "ADANIPORTS", "AXISBANK", "BAJFINANCE", "BHARTIARTL", 
    "BPCL", "CIPLA", "HDFCBANK", "ICICIBANK", "INFY", "ITC", "LT", "M&M", "RELIANCE", "SBIN", "TCS", 
    "TATAMOTORS", "TITAN", "WIPRO", "ZOMATO", "HAL", "TRENT", "BEL", "NTPC", "ONGC", "POWERGRID"
] # (You can add all 200 stocks here)

def add_indicators(df):
    df = df.copy()
    if df.empty or len(df) < 30: return pd.DataFrame()
    df['DATE_ONLY'] = df.index.date
    df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['PV'] = df['Close'] * df['Volume']
    df['VWAP'] = df.groupby('DATE_ONLY')['PV'].cumsum() / (df.groupby('DATE_ONLY')['Volume'].cumsum() + 1e-9)
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
    # Backtest కోసం 6 రోజుల డేటా
    d15m = yf.download(tickers, period="6d", interval="15m", group_by="ticker", progress=False)
    d1h = yf.download("^NSEI", period="6d", interval="1h", progress=False)
    return d15m, d1h

# =========================================================
# 3. SCAN ENGINE
# =========================================================
def scan_stock_logic(stock, data_15m, nifty_15m, market_trend, is_backtest=False):
    try:
        ticker = stock + ".NS"
        stock_raw = data_15m[ticker].dropna()
        df = add_indicators(stock_raw)
        if df.empty: return []
        
        results = []
        today_date = now.date()
        # Backtest అయితే మొత్తం డేటా, లేకపోతే కేవలం ఈరోజు
        scan_df = df if is_backtest else df[df.index.date == today_date]
        
        for i in range(len(scan_df)):
            idx = df.index.get_loc(scan_df.index[i])
            if idx < 1: continue
            
            row, prev = df.iloc[idx], df.iloc[idx-1]
            n_row = nifty_15m.reindex(df.index, method='ffill').iloc[idx]
            
            cross_up = (prev['EMA9'] < prev['VWAP']) and (row['EMA9'] > row['VWAP'])
            cross_down = (prev['EMA9'] > prev['VWAP']) and (row['EMA9'] < row['VWAP'])
            
            if market_trend == "POSITIVE" and n_row['Close'] > n_row['EMA20']:
                if (cross_up or row['EMA9'] > row['VWAP']) and row['RSI'] > 55 and row['MACD'] > row['MACD_SIGNAL']:
                    results.append({"DATE": row.name.strftime('%d-%b'), "TIME": row.name.strftime('%H:%M'), "STOCK": stock, "SIGNAL": "BUY", "PRICE": round(row['Close'], 2), "RVOL": round(row['RVOL'], 2), "ATR": round(row['ATR'], 2)})
            
            elif market_trend == "NEGATIVE" and n_row['Close'] < n_row['EMA20']:
                if (cross_down or row['EMA9'] < row['VWAP']) and row['RSI'] < 45 and row['MACD'] < row['MACD_SIGNAL']:
                    results.append({"DATE": row.name.strftime('%d-%b'), "TIME": row.name.strftime('%H:%M'), "STOCK": stock, "SIGNAL": "SELL", "PRICE": round(row['Close'], 2), "RVOL": round(row['RVOL'], 2), "ATR": round(row['ATR'], 2)})
        return results
    except: return []

# =========================================================
# 4. EXECUTION & TABS
# =========================================================
d15m, d1h = fetch_data()
market_trend = "UNKNOWN"
nifty_15m = pd.DataFrame()

if not d1h.empty:
    n_last_1h = d1h['Close'].iloc[-1]
    n_ema_1h = d1h['Close'].ewm(span=20, adjust=False).mean().iloc[-1]
    market_trend = "POSITIVE" if n_last_1h > n_ema_1h else "NEGATIVE"
    n_raw = d15m["^NSEI"].dropna()
    if not n_raw.empty: nifty_15m = add_indicators(n_raw)
    
    box_class = "pos-trend" if market_trend == "POSITIVE" else "neg-trend"
    st.markdown(f'<div class="nifty-box {box_class}">NIFTY 50 1-HOUR TREND: {market_trend}</div>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🔍 LIVE TRACKER (Today)", "📊 5-DAY BACKTEST"])

with tab1:
    if st.button("🚀 START LIVE SCAN"):
        with st.spinner("Analyzing Today's Market..."):
            with ThreadPoolExecutor(max_workers=30) as executor:
                all_res = list(executor.map(lambda s: scan_stock_logic(s, d15m, nifty_15m, market_trend), stocks))
            flat_res = [item for sublist in all_res for item in sublist]
            if flat_res:
                df_live = pd.DataFrame(flat_res).sort_values(by="TIME", ascending=False)
                st.dataframe(df_live.drop(columns=['DATE', 'ATR']), use_container_width=True)
                # Excel Download
                out = io.BytesIO()
                df_live.to_excel(out, index=False)
                st.download_button("📥 Download Today's Report", out.getvalue(), f"Today_Signals_{now.strftime('%d%m')}.xlsx")
            else: st.info("No signals found for today.")

with tab2:
    if st.button("📊 RUN BACKTEST"):
        with st.spinner("Analyzing 5-Day Data..."):
            with ThreadPoolExecutor(max_workers=30) as executor:
                all_bt = list(executor.map(lambda s: scan_stock_logic(s, d15m, nifty_15m, market_trend, is_backtest=True), stocks))
            flat_bt = [item for sublist in all_bt for item in sublist]
            if flat_bt:
                df_bt = pd.DataFrame(flat_bt).sort_values(by=["DATE", "TIME"], ascending=False)
                st.dataframe(df_bt.drop(columns=['ATR']), use_container_width=True)
                # Excel Download
                out_bt = io.BytesIO()
                df_bt.to_excel(out_bt, index=False)
                st.download_button("📥 Download Backtest Excel", out_bt.getvalue(), "Backtest_5Day_Report.xlsx")
            else: st.info("No historical signals found.")
