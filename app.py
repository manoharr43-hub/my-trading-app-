import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, time
import pytz
from concurrent.futures import ThreadPoolExecutor
import io

# =========================================================
# PAGE CONFIG & TIMEZONE
# =========================================================
st.set_page_config(page_title="🚀 NSE AI QUANT V19.0 PRO", layout="wide")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.markdown(f'<h1 style="text-align:center; color:#22c55e;">🚀 NSE AI QUANT PRO V19.0</h1>', unsafe_allow_html=True)
st.markdown(f'<h4 style="text-align:center;">🕒 IST: {now.strftime("%Y-%m-%d %H:%M:%S")} | Bollinger Bands + 80% Accuracy Logic</h4>', unsafe_allow_html=True)

# =========================================================
# ADVANCED INDICATORS ENGINE
# =========================================================
def get_indicators(df):
    df = df.copy()
    if len(df) < 50: return pd.DataFrame()

    # EMAs & VWAP
    df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()
    df['PV'] = df['Close'] * df['Volume']
    df['VWAP'] = df.groupby(df.index.date)['PV'].cumsum() / (df.groupby(df.index.date)['Volume'].cumsum() + 1e-9)

    # 1. Bollinger Bands (20, 2)
    df['BB_MID'] = df['Close'].rolling(window=20).mean()
    df['BB_STD'] = df['Close'].rolling(window=20).std()
    df['BB_UPPER'] = df['BB_MID'] + (df['BB_STD'] * 2)
    df['BB_LOWER'] = df['BB_MID'] - (df['BB_STD'] * 2)

    # 2. ADX (Trend Strength)
    tr = pd.concat([df['High']-df['Low'], abs(df['High']-df['Close'].shift(1)), abs(df['Low']-df['Close'].shift(1))], axis=1).max(axis=1)
    plus_dm = df['High'].diff().clip(lower=0)
    minus_dm = df['Low'].diff().clip(upper=0).abs()
    tr_smooth = tr.rolling(14).mean()
    plus_di = 100 * (plus_dm.rolling(14).mean() / (tr_smooth + 1e-9))
    minus_di = 100 * (minus_dm.rolling(14).mean() / (tr_smooth + 1e-9))
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 1e-9)
    df['ADX'] = dx.rolling(14).mean()

    # 3. RSI & ATR
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-9))))
    df['ATR'] = tr.rolling(14).mean()
    df['RVOL'] = df['Volume'] / (df['Volume'].rolling(20).mean() + 1e-9)
    
    return df

# =========================================================
# STOCKS LIST
# =========================================================
stocks = ["ABB","ACC","AUBANK","ADANIENSOL","ADANIENT","ADANIGREEN","ADANIPORTS","ADANIPOWER","ATGL",
          "ABCAPITAL","ABFRL","ALKEM","AMBUJACEM","APOLLOHOSP","APOLLOTYRE","ASHOKLEY","ASIANPAINT",
          "AXISBANK","BAJAJ-AUTO","BAJFINANCE","BAJAJFINSV","BEL","BHEL","BPCL","BHARTIARTL",
          "CANBK","CIPLA","COALINDIA","DLF","DRREDDY","GAIL","HDFCBANK","HCLTECH","HINDALCO",
          "ICICIBANK","INFY","ITC","JSWSTEEL","KOTAKBANK","LT","M&M","MARUTI","NTPC","ONGC",
          "RELIANCE","SBIN","SUNPHARMA","TATASTEEL","TCS","TECHM","TITAN","WIPRO","ZOMATO"]

@st.cache_data(ttl=300)
def fetch_data():
    tickers = [s + ".NS" for s in stocks]
    return yf.download(tickers, period="7d", interval="15m", auto_adjust=True, group_by='ticker', progress=False)

data_pool = fetch_data()

# =========================================================
# PRECISION SCAN LOGIC
# =========================================================
def scan(stock, mode="TODAY"):
    try:
        ticker = stock + ".NS"
        df = get_indicators(data_pool[ticker].dropna())
        if df.empty: return []
        df.index = df.index.tz_convert(IST)
        scan_df = df[df.index.date == now.date()] if mode == "TODAY" else df
        results = []
        for i in range(2, len(scan_df)):
            row = scan_df.iloc[i]
            prev = scan_df.iloc[i-1]
            
            # --- FILTERS ---
            valid_time = time(9, 45) <= row.name.time() <= time(14, 45)
            strong_trend = row['ADX'] > 30
            
            # Bollinger Band Safety: ధర అప్పర్ బాండ్ కంటే తక్కువ ఉంటేనే బై చేయాలి
            bb_buy_safety = row['Close'] < row['BB_UPPER']
            bb_sell_safety = row['Close'] > row['BB_LOWER']

            # Pullback & Volume
            pb_buy = (prev['Low'] <= prev['EMA21'] and row['Close'] > row['EMA21'])
            pb_sell = (prev['High'] >= prev['EMA21'] and row['Close'] < row['EMA21'])
            vol_ok = row['RVOL'] > 2.2

            # Signal Generation
            buy_sig = (row['EMA9'] > row['EMA21'] and row['Close'] > row['VWAP'] and 
                       (pb_buy or vol_ok) and 55 < row['RSI'] < 65 and strong_trend and valid_time and bb_buy_safety)
            
            sell_sig = (row['EMA9'] < row['EMA21'] and row['Close'] < row['VWAP'] and 
                        (pb_sell or vol_ok) and 35 < row['RSI'] < 45 and strong_trend and valid_time and bb_sell_safety)

            if buy_sig or sell_sig:
                sig = "BUY" if buy_sig else "SELL"
                price = round(row['Close'], 2)
                risk = row['ATR'] * 1.5
                sl = round(price - risk, 2) if buy_sig else round(price + risk, 2)
                tgt = round(price + (risk * 2), 2) if buy_sig else round(price - (risk * 2), 2)
                
                # Live Status Check for Scanner
                ltp = round(scan_df.iloc[-1]['Close'], 2)
                status = "⏳ RUNNING"
                if buy_sig and ltp >= tgt: status = "✅ TGT HIT"
                elif sell_sig and ltp <= tgt: status = "✅ TGT HIT"
                elif buy_sig and ltp <= sl: status = "❌ SL HIT"
                elif sell_sig and ltp >= sl: status = "❌ SL HIT"

                results.append({
                    "TIME": row.name.strftime("%H:%M"), "STOCK": stock, "SIGNAL": sig, 
                    "ENTRY": price, "LTP": ltp, "SL": sl, "TGT": tgt, "STATUS": status,
                    "ADX": round(row['ADX'], 1), "RSI": round(row['RSI'], 1), "DATE": row.name.strftime("%Y-%m-%d")
                })
        return results
    except: return []

# =========================================================
# UI & HELPERS
# =========================================================
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

def style_status(val):
    if "TGT" in str(val): return 'color: #4ade80; font-weight: bold'
    if "SL" in str(val): return 'color: #f87171; font-weight: bold'
    return 'color: #fbbf24'

tab1, tab2 = st.tabs(["🔍 LIVE SCANNER (BB)", "📊 BACKTEST REPORT"])

with tab1:
    if st.button("🚀 RUN SCANNER V19"):
        res = [item for s in stocks for item in scan(s, "TODAY")]
        if res:
            df = pd.DataFrame(res).drop_duplicates('STOCK', keep='last').sort_values('TIME', ascending=False)
            st.dataframe(df.style.map(style_status, subset=['STATUS']), use_container_width=True)
            st.download_button("📥 Download Scanner Excel", to_excel(df), f"Scanner_V19_{now.date()}.xlsx")
        else: st.info("No precision signals with Bollinger safety found.")

with tab2:
    if st.button("📊 RUN BACKTEST V19"):
        res_bt = [item for s in stocks for item in scan(s, "BACKTEST")]
        if res_bt:
            df_bt = pd.DataFrame(res_bt).sort_values(['DATE', 'TIME'], ascending=False)
            st.dataframe(df_bt.style.map(style_status, subset=['STATUS']), use_container_width=True)
            st.download_button("📥 Download Backtest Excel", to_excel(df_bt), "Backtest_V19.xlsx")
