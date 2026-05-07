# =========================================================
# 🚀 NSE AI QUANT PRO V14.0 - ULTRA GOLD (ENHANCED)
# EMA9 + VWAP + RSI + RVOL + ADX + ATR SL
# =========================================================

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
from concurrent.futures import ThreadPoolExecutor
import io
import pandas_ta as ta  # Technical Analysis library

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="🚀 NSE AI QUANT PRO V14.0",
    layout="wide"
)

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

# =========================================================
# CUSTOM CSS
# =========================================================
st.markdown("""
<style>
.main-title{text-align:center; font-size:42px; font-weight:bold; color:#22c55e;}
.sub-title{text-align:center; font-size:18px; color:#cbd5e1; margin-bottom:20px;}
.market-box{padding:20px; border-radius:12px; text-align:center; font-size:24px; font-weight:bold; margin-bottom:20px;}
.bull{background:#052e16; color:#22c55e; border:2px solid #22c55e;}
.bear{background:#450a0a; color:#f87171; border:2px solid #f87171;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🚀 NSE AI QUANT PRO V14.0 ULTRA GOLD</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-title">🕒 LIVE TIME : {now.strftime("%H:%M:%S")} IST</div>', unsafe_allow_html=True)

# =========================================================
# STOCKS LIST
# =========================================================
stocks = [
    "ABB","ACC","AUBANK","ADANIENSOL","ADANIENT","ADANIGREEN","ADANIPORTS","ADANIPOWER","ATGL",
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
    "YESBANK","ZEEL","ZOMATO"
]

# =========================================================
# INDICATORS ENGINE
# =========================================================
def add_indicators(df):
    if df.empty or len(df) < 30: return pd.DataFrame()
    
    df = df.copy()
    # EMA
    df['EMA9'] = ta.ema(df['Close'], length=9)
    df['EMA20'] = ta.ema(df['Close'], length=20)
    
    # VWAP
    df.index = pd.to_datetime(df.index)
    df['VWAP'] = ta.vwap(high=df['High'], low=df['Low'], close=df['Close'], volume=df['Volume'])
    
    # RSI
    df['RSI'] = ta.rsi(df['Close'], length=14)
    
    # ADX (Trend Strength)
    adx_df = ta.adx(df['High'], df['Low'], df['Close'], length=14)
    df = pd.concat([df, adx_df], axis=1)
    
    # ATR (for Stop Loss)
    df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
    
    # RVOL
    df['VOLAVG'] = df['Volume'].rolling(20).mean()
    df['RVOL'] = df['Volume'] / (df['VOLAVG'] + 1e-9)
    
    return df

# =========================================================
# FAST DATA FETCH
# =========================================================
@st.cache_data(ttl=60)
def fetch_all_data():
    tickers = [s + ".NS" for s in stocks]
    tickers.append("^NSEI")
    # Fetching all stocks at once is much faster
    data = yf.download(tickers, period="7d", interval="15m", auto_adjust=True, group_by='ticker')
    return data

full_data = fetch_all_data()

# =========================================================
# MARKET TREND
# =========================================================
try:
    nifty_raw = full_data["^NSEI"].dropna()
    nifty_ema20 = ta.ema(nifty_raw['Close'], length=20).iloc[-1]
    nifty_last = nifty_raw['Close'].iloc[-1]
    market_trend = "POSITIVE" if nifty_last > nifty_ema20 else "NEGATIVE"
    box_class = "bull" if market_trend == "POSITIVE" else "bear"
    st.markdown(f'<div class="market-box {box_class}">📈 NIFTY TREND : {market_trend}</div>', unsafe_allow_html=True)
except:
    st.error("Market Trend calculation failed.")

# =========================================================
# SCAN ENGINE
# =========================================================
def scan_stock(stock, is_backtest=False):
    try:
        ticker = stock + ".NS"
        df = add_indicators(full_data[ticker].dropna())
        if df.empty: return []

        results = []
        # Filter for today or backtest
        if not is_backtest:
            scan_df = df[df.index.date == now.date()]
        else:
            scan_df = df.iloc[30:] # Skip warm-up period

        for i in range(1, len(scan_df)):
            row = scan_df.iloc[i]
            prev = scan_df.iloc[i-1]
            
            # ADX > 20 means trend is strong
            # BUY SIGNAL
            buy_signal = (
                row['EMA9'] > row['VWAP'] and prev['EMA9'] <= prev['VWAP'] and
                row['RSI'] > 50 and row['ADX_14'] > 20 and row['RVOL'] > 1.2
            )
            
            # SELL SIGNAL
            sell_signal = (
                row['EMA9'] < row['VWAP'] and prev['EMA9'] >= prev['VWAP'] and
                row['RSI'] < 50 and row['ADX_14'] > 20 and row['RVOL'] > 1.2
            )

            if buy_signal or sell_signal:
                sig_type = "BUY" if buy_signal else "SELL"
                # Stop Loss Calculation
                sl_val = row['Close'] - (row['ATR'] * 1.5) if buy_signal else row['Close'] + (row['ATR'] * 1.5)
                
                results.append({
                    "DATE": row.name.strftime("%d-%b"),
                    "TIME": row.name.strftime("%H:%M"),
                    "STOCK": stock,
                    "SIGNAL": sig_type,
                    "PRICE": round(row['Close'], 2),
                    "SL": round(sl_val, 2),
                    "TGT": round(row['Close'] + (row['Close'] - sl_val) * 2, 2), # 1:2 Risk Reward
                    "RSI": round(row['RSI'], 1),
                    "ADX": round(row['ADX_14'], 1),
                    "RVOL": round(row['RVOL'], 1)
                })
        return results
    except: return []

# =========================================================
# TABS & UI
# =========================================================
tab1, tab2 = st.tabs(["🔍 TODAY SCANNER", "📊 5 DAY BACKTEST"])

with tab1:
    if st.button("🚀 RUN V14 SCANNER"):
        with st.spinner("Analyzing Market Strength..."):
            with ThreadPoolExecutor(max_workers=20) as executor:
                all_results = list(executor.map(lambda s: scan_stock(s), stocks))
            
            flat_results = [item for sublist in all_results for item in sublist]
            if flat_results:
                df_live = pd.DataFrame(flat_results).drop_duplicates(subset=['STOCK'], keep='last')
                df_live = df_live.sort_values(by="TIME", ascending=False)
                
                c1, c2, c3 = st.columns(3)
                c1.metric("TOTAL", len(df_live))
                c2.metric("BUY", len(df_live[df_live['SIGNAL']=="BUY"]))
                c3.metric("SELL", len(df_live[df_live['SIGNAL']=="SELL"]))
                
                st.dataframe(df_live, use_container_width=True)
            else:
                st.warning("No Strong Trend Signals Found.")

with tab2:
    if st.button("📊 RUN BACKTEST"):
        with st.spinner("Reviewing Last 5 Days..."):
            with ThreadPoolExecutor(max_workers=20) as executor:
                all_bt = list(executor.map(lambda s: scan_stock(s, True), stocks))
            
            flat_bt = [item for sublist in all_bt for item in sublist]
            if flat_bt:
                df_bt = pd.DataFrame(flat_bt)
                st.success(f"Signals Found: {len(df_bt)}")
                st.dataframe(df_bt, use_container_width=True)
            else:
                st.warning("No Backtest Data.")
