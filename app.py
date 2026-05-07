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
    page_title="🚀 NSE AI QUANT PRO V23 - NIFTY 200",
    layout="wide"
)

# =========================================================
# TIMEZONE & THEME
# =========================================================
IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.markdown("""
    <style>
    .main { background-color: #0f172a; color: white; }
    .stMetric { background-color: #1e293b; padding: 15px; border-radius: 10px; border: 1px solid #334155; }
    </style>
    """, unsafe_allow_html=True)

# =========================================================
# NIFTY 200 STOCK LIST (Major Stocks)
# =========================================================
# సమయం ఆదా చేయడానికి ప్రధాన నిఫ్టీ 200 స్టాక్స్ ఇక్కడ ఉన్నాయి
nifty_200_stocks = [
    "ABB","ACC","AUBANK","ADANIENSOL","ADANIENT","ADANIGREEN","ADANIPORTS","ADANIPOWER","ATGL","ABCAPITAL",
    "ABFRL","ALKEM","AMBUJACEM","APOLLOHOSP","APOLLOTYRE","ASHOKLEY","ASIANPAINT","AXISBANK","BAJAJ-AUTO",
    "BAJFINANCE","BAJAJFINSV","BEL","BHEL","BPCL","BHARTIARTL","CANBK","CIPLA","COALINDIA","DLF","DRREDDY",
    "GAIL","HDFCBANK","HCLTECH","HINDALCO","ICICIBANK","INFY","ITC","JSWSTEEL","KOTAKBANK","LT","M&M",
    "MARUTI","NTPC","ONGC","RELIANCE","SBIN","SUNPHARMA","TATASTEEL","TCS","TECHM","TITAN","WIPRO","ZOMATO",
    "AMARAJABAT","APLLTD","AUROPHARMA","BALKRISIND","BANDHANBNK","BANKBARODA","BERGEPAINT","BIOCON","CHOLAFIN",
    "CONCOR","CUMMINSIND","ESCORTS","FEDERALBNK","GODREJCP","GUJGASLTD","HAVELLS","HEROMOTOCO","HIND-UNILVR",
    "ICICIGI","IDFCFIRSTB","IGL","INDHOTEL","INDUSINDBK","INDUSTOWER","IOC","IRCTC","JINDALSTEL","JUBLFOOD",
    "LICHSGFIN","LTIM","LUPIN","MRF","MUTHOOTFIN","NAUKRI","NESTLEIND","OBEROIRLTY","PEL","PFC","PIDILITIND",
    "PNB","RECLTD","SRF","TATACOMM","TATACONSUM","TATAMOTORS","TATAPOWER","TRENT","TVSMOTOR","UBL","ULTRACEMCO",
    "UPL","VOLTAS","YESBANK"
] # మరిన్ని యాడ్ చేసుకోవచ్చు

# =========================================================
# INDICATORS CALCULATOR
# =========================================================
def calculate_v23_indicators(df):
    df = df.copy().ffill()
    if len(df) < 50: return pd.DataFrame()

    # EMAs
    df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()

    # VWAP
    df['PV'] = df['Close'] * df['Volume']
    df['VWAP'] = (df.groupby(df.index.date)['PV'].cumsum() / (df.groupby(df.index.date)['Volume'].cumsum() + 1e-9))

    # RSI & ADX
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = ((-delta.where(delta < 0, 0))).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-9))))
    
    tr = pd.concat([df['High']-df['Low'], abs(df['High']-df['Close'].shift(1)), abs(df['Low']-df['Close'].shift(1))], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()
    
    # RVOL
    df['RVOL'] = df['Volume'] / (df['Volume'].rolling(20).mean() + 1e-9)

    return df

# =========================================================
# CORE SCANNER LOGIC
# =========================================================
def run_v23_engine(stock, mode="TODAY", raw_data=None):
    try:
        ticker = stock + ".NS"
        df = calculate_v23_indicators(raw_data[ticker].dropna())
        if df.empty: return []

        if df.index.tz is None: df.index = df.index.tz_localize("UTC")
        df.index = df.index.tz_convert(IST)

        scan_df = df[df.index.date == df.index.date.max()] if mode == "TODAY" else df.copy()
        
        results = []
        for i in range(5, len(scan_df) - 5):
            row = scan_df.iloc[i]
            
            # V23 PRO CONDITIONS
            buy_sig = (row['Close'] > row['EMA50'] and row['EMA9'] > row['EMA21'] and 
                       row['Close'] > row['VWAP'] and 55 < row['RSI'] < 75)
            
            sell_sig = (row['Close'] < row['EMA50'] and row['EMA9'] < row['EMA21'] and 
                        row['Close'] < row['VWAP'] and 25 < row['RSI'] < 45)

            if buy_sig or sell_sig:
                signal = "BUY" if buy_sig else "SELL"
                entry = round(row['Close'], 2)
                sl = round(entry - (row['ATR'] * 1.5), 2) if buy_sig else round(entry + (row['ATR'] * 1.5), 2)
                tgt = round(entry + (row['ATR'] * 3), 2) if buy_sig else round(entry - (row['ATR'] * 3), 2)

                # Outcome Simulation
                status = "⏳ OPEN"
                future = scan_df.iloc[i+1 : i+10]
                for _, frow in future.iterrows():
                    if buy_sig:
                        if frow['High'] >= tgt: status = "✅ TARGET"; break
                        if frow['Low'] <= sl: status = "❌ SL"; break
                    else:
                        if frow['Low'] <= tgt: status = "✅ TARGET"; break
                        if frow['High'] >= sl: status = "❌ SL"; break

                results.append({
                    "DATE": row.name.strftime("%Y-%m-%d"),
                    "TIME": row.name.strftime("%H:%M"),
                    "STOCK": stock, "SIGNAL": signal, "ENTRY": entry,
                    "SL": sl, "TGT": tgt, "STATUS": status,
                    "RVOL": round(row['RVOL'], 2)
                })
        return results
    except: return []

# =========================================================
# MAIN INTERFACE
# =========================================================
st.title("🚀 NSE AI QUANT PRO V23 (NIFTY 200)")

tab1, tab2 = st.tabs(["🔍 MULTI-STOCK SCANNER", "📊 BACKTEST DASHBOARD"])

@st.cache_data(ttl=600)
def load_bulk_data():
    tickers = [s + ".NS" for s in nifty_200_stocks]
    return yf.download(tickers, period="1mo", interval="15m", group_by="ticker", auto_adjust=True, threads=True)

all_data = load_bulk_data()

with tab1:
    if st.button("🔥 START NIFTY 200 SCAN"):
        with st.spinner(f"Scanning {len(nifty_200_stocks)} Stocks..."):
            today_res = []
            with ThreadPoolExecutor(max_workers=15) as executor:
                futures = [executor.submit(run_v23_engine, s, "TODAY", all_data) for s in nifty_200_stocks]
                for f in futures: today_res.extend(f.result())
            
            if today_res:
                st.success(f"Found {len(today_res)} Signals")
                st.dataframe(pd.DataFrame(today_res), use_container_width=True)
            else:
                st.warning("ప్రస్తుతానికి ఎటువంటి హై-ప్రాబబిలిటీ సిగ్నల్స్ లేవు.")

with tab2:
    if st.button("📊 GENERATE BACKTEST REPORT"):
        with st.spinner("Analyzing past 30 days performance..."):
            bt_res = []
            with ThreadPoolExecutor(max_workers=15) as executor:
                futures = [executor.submit(run_v23_engine, s, "BACKTEST", all_data) for s in nifty_200_stocks]
                for f in futures: bt_res.extend(f.result())
            
            if bt_res:
                df_bt = pd.DataFrame(bt_res)
                wins = len(df_bt[df_bt['STATUS'] == "✅ TARGET"])
                losses = len(df_bt[df_bt['STATUS'] == "❌ SL"])
                acc = (wins / (wins + losses) * 100) if (wins+losses) > 0 else 0
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Win Accuracy", f"{acc:.2f}%")
                c2.metric("Target Hits", wins)
                c3.metric("SL Hits", losses)
                
                st.dataframe(df_bt.sort_values("DATE", ascending=False), use_container_width=True)
            else:
                st.error("No backtest data found.")
