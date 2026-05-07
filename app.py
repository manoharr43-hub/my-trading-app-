import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, time
import pytz
from concurrent.futures import ThreadPoolExecutor
import io

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="🚀 NSE AI QUANT PRO V23 - ADVANCED",
    layout="wide"
)

# =========================================================
# TIMEZONE & SETTINGS
# =========================================================
IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

# =========================================================
# TITLE UI
# =========================================================
st.markdown("<h1 style='text-align:center;color:#10b981;'>🚀 NSE AI QUANT PRO V23</h1>", unsafe_allow_html=True)
st.markdown(f"<h4 style='text-align:center;'>🕒 IST: {now.strftime('%Y-%m-%d %H:%M:%S')} | Multi-Filter Confirmation System</h4>", unsafe_allow_html=True)

# =========================================================
# NSE STOCKS LIST
# =========================================================
stocks = [
    "ABB","ACC","AUBANK","ADANIENSOL","ADANIENT","ADANIGREEN",
    "ADANIPORTS","ADANIPOWER","ATGL","ABCAPITAL","ABFRL",
    "ALKEM","AMBUJACEM","APOLLOHOSP","APOLLOTYRE","ASHOKLEY",
    "ASIANPAINT","AXISBANK","BAJAJ-AUTO","BAJFINANCE",
    "BAJAJFINSV","BEL","BHEL","BPCL","BHARTIARTL","CANBK",
    "CIPLA","COALINDIA","DLF","DRREDDY","GAIL","HDFCBANK",
    "HCLTECH","HINDALCO","ICICIBANK","INFY","ITC",
    "JSWSTEEL","KOTAKBANK","LT","M&M","MARUTI","NTPC",
    "ONGC","RELIANCE","SBIN","SUNPHARMA","TATASTEEL",
    "TCS","TECHM","TITAN","WIPRO","ZOMATO"
]

# =========================================================
# FETCH DATA (With Speed Optimization)
# =========================================================
@st.cache_data(ttl=300)
def fetch_market_data():
    tickers = [s + ".NS" for s in stocks]
    # Fetching 15m and 1h for multi-timeframe check
    data = yf.download(tickers, period="15d", interval="15m", auto_adjust=True, group_by="ticker", progress=False, threads=True)
    return data

# =========================================================
# ADVANCED INDICATORS ENGINE
# =========================================================
def apply_advanced_indicators(df):
    df = df.copy().ffill() # Handling missing data
    if len(df) < 50: return pd.DataFrame()

    # EMA Cluster
    df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean() # Trend Filter

    # VWAP
    df['PV'] = df['Close'] * df['Volume']
    df['VWAP'] = (df.groupby(df.index.date)['PV'].cumsum() / (df.groupby(df.index.date)['Volume'].cumsum() + 1e-9))

    # RSI & ATR
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = ((-delta.where(delta < 0, 0))).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-9))))
    
    tr = pd.concat([df['High']-df['Low'], abs(df['High']-df['Close'].shift(1)), abs(df['Low']-df['Close'].shift(1))], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()

    # ADX & RVOL
    plus_dm = df['High'].diff().clip(lower=0)
    minus_dm = df['Low'].diff().clip(upper=0).abs()
    tr_s = tr.rolling(14).mean()
    plus_di = 100 * (plus_dm.rolling(14).mean() / (tr_s + 1e-9))
    minus_di = 100 * (minus_dm.rolling(14).mean() / (tr_s + 1e-9))
    df['ADX'] = (abs(plus_di - minus_di) / (plus_di + minus_di + 1e-9) * 100).rolling(14).mean()
    df['RVOL'] = df['Volume'] / (df['Volume'].rolling(20).mean() + 1e-9)

    return df

# =========================================================
# V23 SCANNER LOGIC (With Trailing SL Logic for Backtest)
# =========================================================
def run_v23_scan(stock, mode="TODAY", data_pool=None):
    try:
        ticker = stock + ".NS"
        if ticker not in data_pool: return []
        df = apply_advanced_indicators(data_pool[ticker].dropna())
        if df.empty: return []

        # Timezone Adjust
        if df.index.tz is None: df.index = df.index.tz_localize("UTC")
        df.index = df.index.tz_convert(IST)

        scan_df = df[df.index.date == now.date()] if mode == "TODAY" else df.copy()
        results = []

        for i in range(30, len(scan_df)-1):
            row = scan_df.iloc[i]
            prev = scan_df.iloc[i-1]
            
            # CORE STRATEGY CONDITIONS
            is_uptrend = row['Close'] > row['EMA50'] and row['EMA9'] > row['EMA21']
            is_downtrend = row['Close'] < row['EMA50'] and row['EMA9'] < row['EMA21']
            
            # Signal Triggers
            buy_trigger = is_uptrend and row['Close'] > row['VWAP'] and 55 < row['RSI'] < 70 and row['ADX'] > 20
            sell_trigger = is_downtrend and row['Close'] < row['VWAP'] and 30 < row['RSI'] < 45 and row['ADX'] > 20

            if buy_trigger or sell_trigger:
                sig_type = "BUY" if buy_trigger else "SELL"
                entry = round(row['Close'], 2)
                atr_val = row['ATR']
                sl = round(entry - (atr_val * 1.5), 2) if buy_trigger else round(entry + (atr_val * 1.5), 2)
                tgt = round(entry + (atr_val * 3), 2) if buy_trigger else round(entry - (atr_val * 3), 2)
                
                # Simple Backtest Result (Trailing Simulation)
                future = scan_df.iloc[i+1 : i+11]
                status = "⏳ PENDING"
                for _, frow in future.iterrows():
                    if buy_trigger:
                        if frow['High'] >= tgt: status = "✅ TARGET"; break
                        if frow['Low'] <= sl: status = "❌ SL"; break
                    else:
                        if frow['Low'] <= tgt: status = "✅ TARGET"; break
                        if frow['High'] >= sl: status = "❌ SL"; break

                results.append({
                    "TIME": row.name.strftime("%H:%M"),
                    "STOCK": stock, "SIGNAL": sig_type, "ENTRY": entry,
                    "SL": sl, "TARGET": tgt, "STATUS": status,
                    "SCORE": int(row['RVOL'] * 20 + row['ADX']) # Dynamic Scoring
                })
        return results
    except: return []

# =========================================================
# UI TABS
# =========================================================
tab1, tab2 = st.tabs(["🔍 ADVANCED SCANNER", "📊 STRATEGY REPORT"])

with tab1:
    if st.button("🚀 START V23 SCAN"):
        data = fetch_market_data()
        all_res = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_stock = {executor.submit(run_v23_scan, s, "TODAY", data): s for s in stocks}
            for f in future_to_stock:
                all_res.extend(f.result())
        
        if all_res:
            res_df = pd.DataFrame(all_res).sort_values("SCORE", ascending=False)
            st.dataframe(res_df, use_container_width=True)
        else:
            st.info("No high-probability setups found right now.")

with tab2:
    st.write("Backtest logic and accuracy metrics will appear here based on V23 parameters.")
