import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
from concurrent.futures import ThreadPoolExecutor
import io

# =========================================================
# PAGE CONFIG & TIMEZONE
# =========================================================
st.set_page_config(page_title="🚀 NSE AI QUANT V15.1 PRO", layout="wide")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.markdown(f'<h1 style="text-align:center; color:#22c55e;">🚀 NSE AI QUANT PRO V15.1</h1>', unsafe_allow_html=True)
st.markdown(f'<h4 style="text-align:center;">🕒 IST: {now.strftime("%Y-%m-%d %H:%M:%S")} | Mode: EMA 21 + Institutional Flow</h4>', unsafe_allow_html=True)

# =========================================================
# INDICATORS ENGINE
# =========================================================
def get_indicators(df):
    df = df.copy()
    if len(df) < 35: return pd.DataFrame()

    # EMAs & VWAP
    df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()
    
    df['PV'] = df['Close'] * df['Volume']
    df['VWAP'] = df.groupby(df.index.date)['PV'].cumsum() / (df.groupby(df.index.date)['Volume'].cumsum() + 1e-9)

    # RSI & ATR
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-9))))

    high_low = df['High'] - df['Low']
    high_cp = np.abs(df['High'] - df['Close'].shift())
    low_cp = np.abs(df['Low'] - df['Close'].shift())
    df['TR'] = pd.concat([high_low, high_cp, low_cp], axis=1).max(axis=1)
    df['ATR'] = df['TR'].rolling(14).mean()

    # Volume & Body Analysis
    df['VOLAVG'] = df['Volume'].rolling(20).mean()
    df['RVOL'] = df['Volume'] / (df['VOLAVG'] + 1e-9)
    df['BODY'] = abs(df['Close'] - df['Open'])
    df['BODY_AVG'] = df['BODY'].rolling(10).mean()

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
# SCAN LOGIC
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

            # 1. BIG PLAYER ENTRY
            big_player = (row['RVOL'] > 2.0 and row['BODY'] > (1.5 * row['BODY_AVG']))

            # 2. EMA 21 PULLBACK
            pb_buy = (prev['Low'] > prev['EMA21'] and row['Low'] <= row['EMA21'] and row['Close'] > row['EMA21'])
            pb_sell = (prev['High'] < prev['EMA21'] and row['High'] >= row['EMA21'] and row['Close'] < row['EMA21'])

            # 3. TREND CONFIRMATION
            bull_trend = row['EMA9'] > row['EMA21'] and row['Close'] > row['VWAP']
            bear_trend = row['EMA9'] < row['EMA21'] and row['Close'] < row['VWAP']

            buy_sig = (bull_trend and (big_player or pb_buy) and row['RSI'] > 52)
            sell_sig = (bear_trend and (big_player or pb_sell) and row['RSI'] < 48)

            if buy_sig or sell_sig:
                sig_type = "🚀 BIG ENTRY" if big_player else "🔄 PULLBACK"
                signal = "BUY" if buy_sig else "SELL"
                
                risk = row['ATR'] * 1.5
                sl = round(row['Close'] - risk, 2) if buy_sig else round(row['Close'] + risk, 2)
                tgt = round(row['Close'] + (risk * 2), 2) if buy_sig else round(row['Close'] - (risk * 2), 2)

                results.append({
                    "DATE": row.name.strftime("%Y-%m-%d"),
                    "TIME": row.name.strftime("%H:%M"),
                    "STOCK": stock,
                    "TYPE": sig_type,
                    "SIGNAL": signal,
                    "PRICE": round(row['Close'], 2),
                    "SL": sl,
                    "TGT": tgt,
                    "RSI": round(row['RSI'], 1),
                    "RVOL": round(row['RVOL'], 1)
                })
        return results
    except: return []

# =========================================================
# UI & STYLING
# =========================================================
tab1, tab2 = st.tabs(["🔍 LIVE SCANNER", "📊 BACKTEST"])

def get_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Signals')
    return output.getvalue()

def color_signal(val):
    color = '#22c55e' if val == 'BUY' else '#ef4444'
    return f'color: {color}; font-weight: bold'

with tab1:
    if st.button("🚀 RUN V15.1 SCAN"):
        with ThreadPoolExecutor(max_workers=15) as exec:
            res = list(exec.map(lambda s: scan(s, "TODAY"), stocks))
        flat = [i for s in res for i in s]
        if flat:
            df_today = pd.DataFrame(flat).drop_duplicates('STOCK', keep='last').sort_values('TIME', ascending=False)
            
            # ATTRIBUTE ERROR FIX: Using map if available, otherwise applymap
            try:
                st.dataframe(df_today.style.map(color_signal, subset=['SIGNAL']), use_container_width=True)
            except AttributeError:
                st.dataframe(df_today.style.applymap(color_signal, subset=['SIGNAL']), use_container_width=True)
            
            st.download_button("📥 Export Signals", get_excel(df_today), "V15_Signals.xlsx")
        else:
            st.warning("No Big Player or Pullback signals found.")

with tab2:
    if st.button("📊 RUN BACKTEST"):
        with ThreadPoolExecutor(max_workers=15) as exec:
            res_bt = list(exec.map(lambda s: scan(s, "BACKTEST"), stocks))
        flat_bt = [i for s in res_bt for i in s]
        if flat_bt:
            df_bt = pd.DataFrame(flat_bt).sort_values(['DATE', 'TIME'], ascending=False)
            try:
                st.dataframe(df_bt.style.map(color_signal, subset=['SIGNAL']), use_container_width=True)
            except AttributeError:
                st.dataframe(df_bt.style.applymap(color_signal, subset=['SIGNAL']), use_container_width=True)
            st.download_button("📥 Download Report", get_excel(df_bt), "Backtest.xlsx")
