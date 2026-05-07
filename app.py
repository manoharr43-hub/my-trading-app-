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
st.set_page_config(page_title="🚀 NSE AI QUANT V16.0 PRO", layout="wide")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.markdown(f'<h1 style="text-align:center; color:#22c55e;">🚀 NSE AI QUANT PRO V16.0</h1>', unsafe_allow_html=True)
st.markdown(f'<h4 style="text-align:center;">🕒 IST: {now.strftime("%Y-%m-%d %H:%M:%S")} | Target: 80% Win Rate Logic</h4>', unsafe_allow_html=True)

# =========================================================
# ADVANCED INDICATORS ENGINE (ADX + EMA + VWAP)
# =========================================================
def get_indicators(df):
    df = df.copy()
    if len(df) < 45: return pd.DataFrame()

    # Trend Indicators
    df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()
    
    df['PV'] = df['Close'] * df['Volume']
    df['VWAP'] = df.groupby(df.index.date)['PV'].cumsum() / (df.groupby(df.index.date)['Volume'].cumsum() + 1e-9)

    # ADX Calculation (Trend Strength)
    plus_dm = df['High'].diff()
    minus_dm = df['Low'].diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm > 0] = 0
    minus_dm = abs(minus_dm)
    
    tr = pd.concat([df['High'] - df['Low'], 
                    abs(df['High'] - df['Close'].shift(1)), 
                    abs(df['Low'] - df['Close'].shift(1))], axis=1).max(axis=1)
    atr_adx = tr.rolling(14).mean()
    
    plus_di = 100 * (plus_dm.rolling(14).mean() / (atr_adx + 1e-9))
    minus_di = 100 * (minus_dm.rolling(14).mean() / (atr_adx + 1e-9))
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 1e-9)
    df['ADX'] = dx.rolling(14).mean()

    # RSI & ATR
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-9))))
    df['ATR'] = tr.rolling(14).mean()

    # Volume Analysis
    df['VOL_AVG'] = df['Volume'].rolling(20).mean()
    df['RVOL'] = df['Volume'] / (df['VOL_AVG'] + 1e-9)
    
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
    data = yf.download(tickers, period="7d", interval="15m", auto_adjust=True, group_by='ticker', progress=False)
    return data

data_pool = fetch_data()

# =========================================================
# 80% WIN-RATE SCAN LOGIC
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
            
            # --- STRICT FILTERS ---
            # 1. Trend Strength (ADX > 25 is strong)
            strong_trend = row['ADX'] > 25
            
            # 2. Time Filter (9:45 AM to 2:45 PM)
            current_time = row.name.time()
            valid_time = time(9, 45) <= current_time <= time(14, 45)
            
            # 3. Momentum & Pullback
            pb_buy = (prev['Low'] <= prev['EMA21'] and row['Close'] > row['EMA21'])
            pb_sell = (prev['High'] >= prev['EMA21'] and row['Close'] < row['EMA21'])
            
            # 4. Big Player Confirmation
            big_entry = row['RVOL'] > 2.2

            # Signal Generation
            buy_sig = (row['EMA9'] > row['EMA21'] and row['Close'] > row['VWAP'] and 
                       (pb_buy or big_entry) and 52 < row['RSI'] < 70 and strong_trend and valid_time)
            
            sell_sig = (row['EMA9'] < row['EMA21'] and row['Close'] < row['VWAP'] and 
                        (pb_sell or big_entry) and 30 < row['RSI'] < 48 and strong_trend and valid_time)

            if buy_sig or sell_sig:
                signal = "BUY" if buy_sig else "SELL"
                price = round(row['Close'], 2)
                # Tight Stop Loss for 1:2 Reward
                risk = row['ATR'] * 1.5
                sl = round(price - risk, 2) if buy_sig else round(price + risk, 2)
                tgt = round(price + (risk * 2), 2) if buy_sig else round(price - (risk * 2), 2)

                status, pnl = "OPEN", 0.0
                if mode == "BACKTEST":
                    future = scan_df.iloc[i+1 : i+25]
                    for _, f in future.iterrows():
                        if buy_sig:
                            if f['High'] >= tgt: status, pnl = "🎯 TGT DONE", round(tgt - price, 2); break
                            elif f['Low'] <= sl: status, pnl = "🛑 SL HIT", round(sl - price, 2); break
                        else:
                            if f['Low'] <= tgt: status, pnl = "🎯 TGT DONE", round(price - tgt, 2); break
                            elif f['High'] >= sl: status, pnl = "🛑 SL HIT", round(price - sl, 2); break

                results.append({
                    "DATE": row.name.strftime("%Y-%m-%d"),
                    "TIME": row.name.strftime("%H:%M"),
                    "STOCK": stock,
                    "SIGNAL": signal,
                    "PRICE": price,
                    "TGT": tgt,
                    "SL": sl,
                    "RESULT": status,
                    "ADX": round(row['ADX'], 1),
                    "TYPE": "🚀 BIG" if big_entry else "🔄 PB"
                })
        return results
    except: return []

# =========================================================
# UI & EXCEL EXPORT
# =========================================================
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='V16_Report')
    return output.getvalue()

tab1, tab2 = st.tabs(["🔍 ACCURACY SCANNER", "📊 BACKTEST REPORT"])

with tab1:
    if st.button("🚀 START 80% ACCURACY SCAN"):
        with ThreadPoolExecutor(max_workers=15) as exec:
            res = list(exec.map(lambda s: scan(s, "TODAY"), stocks))
        flat = [i for s in res for i in s]
        if flat:
            df_today = pd.DataFrame(flat).drop_duplicates('STOCK', keep='last').sort_values('TIME', ascending=False)
            st.dataframe(df_today, use_container_width=True)
            st.download_button("📥 Excel Download", to_excel(df_today), "Today_V16.xlsx")
        else: st.info("మంచి ట్రెండ్ కోసం ఎదురుచూస్తోంది... ప్రస్తుతం బలమైన సిగ్నల్స్ లేవు.")

with tab2:
    if st.button("📊 RUN V16.0 BACKTEST"):
        with ThreadPoolExecutor(max_workers=15) as exec:
            res_bt = list(exec.map(lambda s: scan(s, "BACKTEST"), stocks))
        flat_bt = [i for s in res_bt for i in s]
        if flat_bt:
            df_bt = pd.DataFrame(flat_bt).sort_values(['DATE', 'TIME'], ascending=False)
            win_count = len(df_bt[df_bt['RESULT'] == "🎯 TGT DONE"])
            total_sig = len(df_bt)
            win_rate = (win_count / total_sig) * 100 if total_sig > 0 else 0
            
            st.subheader(f"Strategy Win Rate: {round(win_rate, 2)}%")
            st.dataframe(df_bt, use_container_width=True)
            st.download_button("📥 Backtest Excel Download", to_excel(df_bt), "Backtest_V16.xlsx")
