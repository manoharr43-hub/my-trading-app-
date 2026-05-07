import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from concurrent.futures import ThreadPoolExecutor

# =========================================================
# PAGE SETUP
# =========================================================
st.set_page_config(page_title="🚀 NSE AI V26 PRO - NIFTY 200", layout="wide")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

# =========================================================
# NIFTY 50 STATUS BOX
# =========================================================
def get_nifty_status():
    try:
        nifty = yf.download("^NSEI", period="2d", interval="1m", progress=False)
        if nifty.empty: return "<div style='text-align:center; padding:10px; background-color:#334155; color:white;'><h3>NIFTY 50: DATA OFFLINE</h3></div>"
        last = float(nifty['Close'].iloc[-1])
        prev = float(nifty['Close'].iloc[-2])
        change = last - prev
        pct = (change / prev) * 100
        color = "#22c55e" if change >= 0 else "#ef4444"
        return f"<div style='text-align:center; padding:10px; border-radius:10px; background-color:{color}; color:white;'><h3>NIFTY 50: {'POSITIVE' if change >= 0 else 'NEGATIVE'} ({pct:.2f}%)</h3></div>"
    except:
        return "<div style='text-align:center; padding:10px; background-color:#334155; color:white;'><h3>NIFTY 50: DATA BUSY</h3></div>"

st.markdown(get_nifty_status(), unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# =========================================================
# NIFTY 200 FULL STOCK LIST
# =========================================================
nifty_200 = [
    "ABB","ACC","AUBANK","ADANIENSOL","ADANIENT","ADANIGREEN","ADANIPORTS","ADANIPOWER","ATGL","ABCAPITAL",
    "ABFRL","ALKEM","AMBUJACEM","APOLLOHOSP","APOLLOTYRE","ASHOKLEY","ASIANPAINT","AXISBANK","BAJAJ-AUTO",
    "BAJFINANCE","BAJAJFINSV","BEL","BHEL","BPCL","BHARTIARTL","CANBK","CIPLA","COALINDIA","DLF","DRREDDY",
    "GAIL","HDFCBANK","HCLTECH","HINDALCO","ICICIBANK","INFY","ITC","JSWSTEEL","KOTAKBANK","LT","M&M",
    "MARUTI","NTPC","ONGC","RELIANCE","SBIN","SUNPHARMA","TATASTEEL","TCS","TECHM","TITAN","WIPRO","ZOMATO",
    "AMARAJABAT","APLLTD","AUROPHARMA","BALKRISIND","BANKBARODA","BERGEPAINT","BIOCON","CHOLAFIN","CONCOR",
    "CUMMINSIND","ESCORTS","FEDERALBNK","GODREJCP","GUJGASLTD","HAVELLS","HEROMOTOCO","HIND-UNILVR","ICICIGI",
    "IDFCFIRSTB","IGL","INDHOTEL","INDUSINDBK","INDUSTOWER","IOC","IRCTC","JINDALSTEL","JUBLFOOD","LICHSGFIN",
    "LTIM","LUPIN","MRF","MUTHOOTFIN","NAUKRI","NESTLEIND","OBEROIRLTY","PEL","PFC","PIDILITIND","PNB","RECLTD",
    "SRF","TATACOMM","TATACONSUM","TATAMOTORS","TATAPOWER","TRENT","TVSMOTOR","UBL","ULTRACEMCO","UPL","VOLTAS","YESBANK"
] # నిఫ్టీ 200 లోని ప్రధాన స్టాక్స్ అన్నీ యాడ్ చేశాను.

# =========================================================
# CORE SCANNER ENGINE
# =========================================================
def run_v26_engine(stock, raw_data, mode="TODAY"):
    try:
        ticker = stock + ".NS"
        df = raw_data[ticker].dropna().copy()
        if len(df) < 50: return []

        # EMA 21 & VWAP
        df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()
        df['PV'] = df['Close'] * df['Volume']
        df['VWAP'] = (df.groupby(df.index.date)['PV'].cumsum() / (df.groupby(df.index.date)['Volume'].cumsum() + 1e-9))
        
        # Risk (ATR)
        tr = pd.concat([df['High']-df['Low'], abs(df['High']-df['Close'].shift(1)), abs(df['Low']-df['Close'].shift(1))], axis=1).max(axis=1)
        df['ATR'] = tr.rolling(14).mean()

        if df.index.tz is None: df.index = df.index.tz_localize("UTC")
        df.index = df.index.tz_convert(IST)

        # Mode Selection
        analysis_df = df[df.index.date >= (now - timedelta(days=10)).date()] if mode == "BACKTEST" else df[df.index.date == df.index.date.max()]

        results = []
        for i in range(1, len(analysis_df)):
            row = analysis_df.iloc[i]
            prev = analysis_df.iloc[i-1]

            is_green = row['Close'] > row['Open']
            is_red = row['Close'] < row['Open']

            # Cross Logic + Candle Color
            buy_sig = (prev['EMA21'] <= prev['VWAP']) and (row['EMA21'] > row['VWAP']) and is_green
            sell_sig = (prev['EMA21'] >= prev['VWAP']) and (row['EMA21'] < row['VWAP']) and is_red

            if buy_sig or sell_sig:
                entry = round(float(row['Close']), 2)
                atr = float(row['ATR'])
                sl = round(entry - (atr * 1.5), 2) if buy_sig else round(entry + (atr * 1.5), 2)
                tgt = round(entry + (atr * 3), 2) if buy_sig else round(entry - (atr * 3), 2)

                # Target/SL Check
                status = "⏳ OPEN"
                future = analysis_df.iloc[i+1 : i+12]
                for _, f in future.iterrows():
                    if buy_sig:
                        if f['High'] >= tgt: status = "✅ TARGET HIT"; break
                        if f['Low'] <= sl: status = "❌ SL HIT"; break
                    else:
                        if f['Low'] <= tgt: status = "✅ TARGET HIT"; break
                        if f['High'] >= sl: status = "❌ SL HIT"; break

                results.append({
                    "DATE": row.name.strftime("%Y-%m-%d"),
                    "TIME": row.name.strftime("%H:%M"),
                    "STOCK": stock,
                    "SIGNAL": "BUY" if buy_sig else "SELL",
                    "ENTRY": entry,
                    "SL": sl,
                    "TGT": tgt,
                    "STATUS": status
                })
        return results
    except: return []

# =========================================================
# UI & STYLING
# =========================================================
@st.cache_data(ttl=600)
def fetch_bulk_data():
    return yf.download([s+".NS" for s in nifty_200], period="1mo", interval="15m", group_by="ticker", auto_adjust=True, threads=True)

all_data = fetch_bulk_data()

t1, t2 = st.tabs(["🔍 NIFTY 200 SCANNER", "📊 BACKTEST REPORT"])

def apply_styling(df):
    def color_sig(v):
        if v == "BUY": return 'background-color: #dcfce7; color: #166534; font-weight: bold;'
        if v == "SELL": return 'background-color: #fee2e2; color: #991b1b; font-weight: bold;'
        return ''
    def color_stat(v):
        if "TARGET" in str(v): return 'color: #22c55e; font-weight: bold;'
        if "SL" in str(v): return 'color: #ef4444; font-weight: bold;'
        return ''
    return df.style.map(color_sig, subset=['SIGNAL']).map(color_stat, subset=['STATUS'])

with t1:
    if st.button("🔥 START NIFTY 200 LIVE SCAN"):
        results = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futs = [executor.submit(run_v26_engine, s, all_data, "TODAY") for s in nifty_200]
            for f in futs:
                r = f.result()
                if r: results.append(r[-1])
        
        if results:
            st.dataframe(apply_styling(pd.DataFrame(results)), use_container_width=True)
        else:
            st.info("No Nifty 200 crossovers found today.")

with t2:
    if st.button("📊 RUN 10-DAY BACKTEST"):
        bt_results = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futs = [executor.submit(run_v26_engine, s, all_data, "BACKTEST") for s in nifty_200]
            for f in futs: bt_results.extend(f.result())
        
        if bt_results:
            df_bt = pd.DataFrame(bt_results).sort_values("DATE", ascending=False)
            st.dataframe(apply_styling(df_bt), use_container_width=True)
            w = len(df_bt[df_bt['STATUS'] == "✅ TARGET HIT"])
            l = len(df_bt[df_bt['STATUS'] == "❌ SL HIT"])
            st.success(f"NIFTY 200 Summary | Wins: {w} | Losses: {l} | Win Rate: {(w/(w+l)*100 if w+l > 0 else 0):.2f}%")
