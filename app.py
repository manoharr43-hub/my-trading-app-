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
st.set_page_config(page_title="🚀 NSE AI QUANT V17.1 PRO", layout="wide")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.markdown(f'<h1 style="text-align:center; color:#22c55e;">🚀 NSE AI QUANT PRO V17.1</h1>', unsafe_allow_html=True)
st.markdown(f'<h4 style="text-align:center;">🕒 IST: {now.strftime("%Y-%m-%d %H:%M:%S")} | Error Fixed & High Precision</h4>', unsafe_allow_html=True)

# =========================================================
# POWER INDICATORS ENGINE
# =========================================================
def get_indicators(df):
    df = df.copy()
    if len(df) < 50: return pd.DataFrame()

    df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()
    df['PV'] = df['Close'] * df['Volume']
    df['VWAP'] = df.groupby(df.index.date)['PV'].cumsum() / (df.groupby(df.index.date)['Volume'].cumsum() + 1e-9)

    # ADX Calculation
    plus_dm = df['High'].diff()
    minus_dm = df['Low'].diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm > 0] = 0
    minus_dm = abs(minus_dm)
    tr = pd.concat([df['High'] - df['Low'], abs(df['High'] - df['Close'].shift(1)), abs(df['Low'] - df['Close'].shift(1))], axis=1).max(axis=1)
    plus_di = 100 * (plus_dm.rolling(14).mean() / (tr.rolling(14).mean() + 1e-9))
    minus_di = 100 * (minus_dm.rolling(14).mean() / (tr.rolling(14).mean() + 1e-9))
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 1e-9)
    df['ADX'] = dx.rolling(14).mean()

    # RSI & ATR
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-9))))
    df['ATR'] = tr.rolling(14).mean()
    df['RVOL'] = df['Volume'] / (df['Volume'].rolling(20).mean() + 1e-9)
    
    return df

# =========================================================
# STOCKS
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
            row, prev = scan_df.iloc[i], scan_df.iloc[i-1]
            valid_time = time(9, 45) <= row.name.time() <= time(14, 45)
            buy_sig = (row['EMA9'] > row['EMA21'] and row['Close'] > row['VWAP'] and row['ADX'] > 30 and 55 < row['RSI'] < 65 and valid_time)
            sell_sig = (row['EMA9'] < row['EMA21'] and row['Close'] < row['VWAP'] and row['ADX'] > 30 and 35 < row['RSI'] < 45 and valid_time)

            if buy_sig or sell_sig:
                sig = "BUY" if buy_sig else "SELL"
                price = round(row['Close'], 2)
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
                results.append({"DATE": row.name.strftime("%Y-%m-%d"), "TIME": row.name.strftime("%H:%M"), "STOCK": stock, "SIGNAL": sig, "PRICE": price, "SL": sl, "TGT": tgt, "RESULT": status, "P&L": pnl})
        return results
    except: return []

# =========================================================
# UI & ERROR FIX (Using .map instead of .applymap)
# =========================================================
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

def color_rows(val):
    if val == "🎯 TGT DONE": return 'color: #4ade80; font-weight: bold'
    if val == "🛑 SL HIT": return 'color: #f87171; font-weight: bold'
    return ''

tab1, tab2 = st.tabs(["🔍 SCANNER", "📊 BACKTEST"])

with tab1:
    if st.button("🚀 RUN SCANNER"):
        res = [item for s in stocks for item in scan(s, "TODAY")]
        if res:
            df = pd.DataFrame(res).drop_duplicates('STOCK', keep='last').sort_values('TIME', ascending=False)
            st.dataframe(df, use_container_width=True)
        else: st.info("No precision signals found.")

with tab2:
    if st.button("📊 RUN BACKTEST"):
        res_bt = [item for s in stocks for item in scan(s, "BACKTEST")]
        if res_bt:
            df_bt = pd.DataFrame(res_bt).sort_values(['DATE', 'TIME'], ascending=False)
            # FIX: Using .map() instead of .applymap() to avoid the error
            try:
                st.dataframe(df_bt.style.map(color_rows, subset=['RESULT']), use_container_width=True)
            except AttributeError:
                st.dataframe(df_bt.style.applymap(color_rows, subset=['RESULT']), use_container_width=True)
            st.download_button("📥 Download Report", to_excel(df_bt), "Backtest_V17.xlsx")
