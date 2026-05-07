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
st.set_page_config(page_title="🚀 NSE AI QUANT PRO V6.9", layout="wide")
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

# 2. NSE 200 LIST
stocks = ["ABB", "ACC", "AUBANK", "ADANIENT", "ADANIPORTS", "AXISBANK", "BAJFINANCE", "BHARTIARTL", "BPCL", "CIPLA", "HDFCBANK", "ICICIBANK", "INFY", "ITC", "LT", "M&M", "RELIANCE", "SBIN", "TCS", "TATAMOTORS", "TITAN", "WIPRO", "ZOMATO", "HAL", "TRENT"] # (Add all NSE 200 stocks here)

# 3. INDICATORS ENGINE
def add_indicators(df):
    df = df.copy()
    if df.empty: return df
    df['Date_Only'] = df.index.date
    df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
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
    return df

@st.cache_data(ttl=60)
def fetch_data():
    tickers = [s + ".NS" for s in stocks] + ["^NSEI"]
    d5 = yf.download(tickers, period="6d", interval="5m", group_by="ticker", progress=False)
    d1h = yf.download("^NSEI", period="5d", interval="1h", progress=False)
    return d5, d1h

# 4. TRADE ANALYSIS LOGIC
def analyze_trade(df, nifty_5m, i, s, n_trend_1h):
    row = df.iloc[i]
    prev = df.iloc[i-1]
    n_row_5m = nifty_5m.reindex(df.index, method='ffill').iloc[i]
    
    cross_up = (prev['EMA9'] < prev['VWAP']) and (row['EMA9'] > row['VWAP'])
    cross_down = (prev['EMA9'] > prev['VWAP']) and (row['EMA9'] < row['VWAP'])
    
    is_healthy = abs((row['Close'] - row['EMA20']) / row['EMA20'] * 100) < 0.85

    if n_trend_1h == "POSITIVE" and n_row_5m['Close'] > n_row_5m['EMA20']:
        if (cross_up or row['EMA9'] > row['VWAP']) and row['RSI'] > 50 and is_healthy:
            if row['RVOL'] > 1.2 and row['Close'] > prev['High']:
                return {"TIME": row.name, "STOCK": s, "SIGNAL": "BUY", "PRICE": round(row['Close'], 2), "RVOL": round(row['RVOL'], 2), "ATR": row['ATR']}

    elif n_trend_1h == "NEGATIVE" and n_row_5m['Close'] < n_row_5m['EMA20']:
        if (cross_down or row['EMA9'] < row['VWAP']) and row['RSI'] < 45 and is_healthy:
            if row['RVOL'] > 1.2 and row['Close'] < prev['Low']:
                return {"TIME": row.name, "STOCK": s, "SIGNAL": "SELL", "PRICE": round(row['Close'], 2), "RVOL": round(row['RVOL'], 2), "ATR": row['ATR']}
    return None

# 5. UI EXECUTION
d5, d1h = fetch_data()
n_ema_1h = d1h['Close'].ewm(span=20, adjust=False).mean().iloc[-1]
n_trend_1h = "POSITIVE" if d1h['Close'].iloc[-1] > n_ema_1h else "NEGATIVE"
nifty_5m = add_indicators(d5["^NSEI"].dropna())

box_class = "pos-trend" if n_trend_1h == "POSITIVE" else "neg-trend"
st.markdown(f'<div class="nifty-box {box_class}">NIFTY 50 1-HOUR TREND: {n_trend_1h}</div>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🔍 LIVE TRACKER", "📊 BACKTEST REPORT"])

with tab1:
    if st.button("🚀 START SCAN"):
        res = []
        for s in stocks:
            try:
                df = add_indicators(d5[s + ".NS"].dropna())
                for i in range(25, len(df)):
                    sig = analyze_trade(df, nifty_5m, i, s, n_trend_1h)
                    if sig:
                        sig['TIME'] = sig['TIME'].astimezone(IST).strftime('%H:%M')
                        res.append(sig)
            except: continue
        if res:
            df_res = pd.DataFrame(res).sort_values(by="TIME", ascending=False)
            st.dataframe(df_res.drop(columns=['ATR']), use_container_width=True)
            # EXCEL DOWNLOAD FOR LIVE
            live_out = io.BytesIO()
            df_res.to_excel(live_out, index=False)
            st.download_button("📥 Download Live Signals (Excel)", live_out.getvalue(), f"Live_Signals_{now.strftime('%d%m')}.xlsx")
        else: st.info("No signals found.")

with tab2:
    if st.button("📊 RUN BACKTEST"):
        bt_list = []
        for s in stocks:
            try:
                df = add_indicators(d5[s + ".NS"].dropna())
                for i in range(25, len(df)-12):
                    sig = analyze_trade(df, nifty_5m, i, s, n_trend_1h)
                    if sig:
                        entry = sig['PRICE']
                        sl = entry - (sig['ATR']*1.5) if sig['SIGNAL']=="BUY" else entry + (sig['ATR']*1.5)
                        tp = entry + (sig['ATR']*2.5) if sig['SIGNAL']=="BUY" else entry - (sig['ATR']*2.5)
                        for j in range(i+1, min(i+40, len(df))):
                            nxt = df.iloc[j]
                            if (sig['SIGNAL']=="BUY" and nxt['Low']<=sl) or (sig['SIGNAL']=="SELL" and nxt['High']>=sl):
                                bt_list.append({"Date": sig['TIME'].strftime('%d-%b'), "Stock": s, "Signal": sig['SIGNAL'], "Result": "LOSS"}); break
                            if (sig['SIGNAL']=="BUY" and nxt['High']>=tp) or (sig['SIGNAL']=="SELL" and nxt['Low']<=tp):
                                bt_list.append({"Date": sig['TIME'].strftime('%d-%b'), "Stock": s, "Signal": sig['SIGNAL'], "Result": "PROFIT"}); break
            except: continue
        if bt_list:
            df_bt = pd.DataFrame(bt_list)
            st.dataframe(df_bt, use_container_width=True)
            # EXCEL DOWNLOAD FOR BACKTEST
            bt_out = io.BytesIO()
            df_bt.to_excel(bt_out, index=False)
            st.download_button("📥 Download Backtest (Excel)", bt_out.getvalue(), "Backtest_V6_9.xlsx")
