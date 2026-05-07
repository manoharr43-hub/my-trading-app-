import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from concurrent.futures import ThreadPoolExecutor
import io

# =========================================================
# PAGE CONFIG & TIMEZONE
# =========================================================
st.set_page_config(page_title="🚀 NSE AI QUANT V14 PRO", layout="wide")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.markdown(f'<h1 style="text-align:center; color:#22c55e;">🚀 NSE AI QUANT PRO V14.0</h1>', unsafe_allow_html=True)
st.markdown(f'<h4 style="text-align:center;">🕒 IST TIME: {now.strftime("%Y-%m-%d %H:%M:%S")}</h4>', unsafe_allow_html=True)

# =========================================================
# INDICATORS ENGINE
# =========================================================
def get_indicators(df):
    df = df.copy()
    if len(df) < 35: return pd.DataFrame()

    # EMA & VWAP
    df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['PV'] = df['Close'] * df['Volume']
    df['VWAP'] = df.groupby(df.index.date)['PV'].cumsum() / (df.groupby(df.index.date)['Volume'].cumsum() + 1e-9)

    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-9))))

    # ATR (Stop Loss కోసం)
    high_low = df['High'] - df['Low']
    high_cp = np.abs(df['High'] - df['Close'].shift())
    low_cp = np.abs(df['Low'] - df['Close'].shift())
    df['TR'] = pd.concat([high_low, high_cp, low_cp], axis=1).max(axis=1)
    df['ATR'] = df['TR'].rolling(14).mean()

    # RVOL
    df['VOLAVG'] = df['Volume'].rolling(20).mean()
    df['RVOL'] = df['Volume'] / (df['VOLAVG'] + 1e-9)

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
    # 7 రోజుల డేటా తీసుకుంటేనే ఇండికేటర్లు కరెక్ట్‌గా వస్తాయి
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

        # Timezone convert to IST
        df.index = df.index.tz_convert(IST)
        
        if mode == "TODAY":
            scan_df = df[df.index.date == now.date()]
        else:
            scan_df = df # Complete 5-7 days for backtest

        results = []
        for i in range(1, len(scan_df)):
            row = scan_df.iloc[i]
            prev = scan_df.iloc[i-1]

            buy = (row['EMA9'] > row['VWAP'] and prev['EMA9'] <= prev['VWAP'] and row['RSI'] > 50 and row['RVOL'] > 1.2)
            sell = (row['EMA9'] < row['VWAP'] and prev['EMA9'] >= prev['VWAP'] and row['RSI'] < 50 and row['RVOL'] > 1.2)

            if buy or sell:
                sig = "BUY" if buy else "SELL"
                sl = row['Close'] - (row['ATR'] * 1.5) if buy else row['Close'] + (row['ATR'] * 1.5)
                results.append({
                    "DATE": row.name.strftime("%Y-%m-%d"),
                    "TIME": row.name.strftime("%H:%M"),
                    "STOCK": stock,
                    "SIGNAL": sig,
                    "PRICE": round(row['Close'], 2),
                    "SL": round(sl, 2),
                    "TGT": round(row['Close'] + (row['Close'] - sl) * 2, 2),
                    "RSI": round(row['RSI'], 1),
                    "RVOL": round(row['RVOL'], 1)
                })
        return results
    except: return []

# =========================================================
# UI TABS
# =========================================================
tab1, tab2 = st.tabs(["🔍 TODAY SCANNER", "📊 BACKTEST REPORT"])

def get_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Signals')
    return output.getvalue()

with tab1:
    if st.button("🚀 RUN TODAY SCAN"):
        with ThreadPoolExecutor(max_workers=15) as exec:
            res = list(exec.map(lambda s: scan(s, "TODAY"), stocks))
        flat = [i for s in res for i in s]
        if flat:
            df_today = pd.DataFrame(flat).drop_duplicates('STOCK', keep='last').sort_values('TIME', ascending=False)
            st.dataframe(df_today, use_container_width=True)
            st.download_button("📥 Download Today Excel", get_excel(df_today), "Today_Signals.xlsx")
        else: st.warning("No signals found for today yet.")

with tab2:
    if st.button("📊 RUN 5-DAY BACKTEST"):
        with ThreadPoolExecutor(max_workers=15) as exec:
            res_bt = list(exec.map(lambda s: scan(s, "BACKTEST"), stocks))
        flat_bt = [i for s in res_bt for i in s]
        if flat_bt:
            df_bt = pd.DataFrame(flat_bt).sort_values(['DATE', 'TIME'], ascending=False)
            st.success(f"Found {len(df_bt)} signals in last 5 days.")
            st.dataframe(df_bt, use_container_width=True)
            st.download_button("📥 Download Backtest Excel", get_excel(df_bt), "Backtest_Report.xlsx")
        else: st.warning("No backtest data found.")
