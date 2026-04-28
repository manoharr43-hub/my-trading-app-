import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from streamlit_autorefresh import st_autorefresh
import io

# =============================
# CONFIG & UI SETUP
# =============================
st.set_page_config(page_title="🚀 NSE AI PRO V43.4", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V43.4 - NSE 200 BIG MOVE SCANNER")
st.write(f"🕒 **Market Time:** {now.strftime('%Y-%m-%d %H:%M:%S')}")

# =============================
# NSE 200 STOCK LIST
# =============================
stocks = [ "RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","AXISBANK","KOTAKBANK","LT","ITC","HINDUNILVR","ASIANPAINT",
           "MARUTI","SUNPHARMA","ONGC","NTPC","POWERGRID","TATASTEEL","JSWSTEEL","BAJFINANCE","BAJAJFINSV","ADANIENT","ADANIPORTS",
           "ULTRACEMCO","GRASIM","TECHM","WIPRO","HCLTECH","NESTLEIND","BRITANNIA","CIPLA","DIVISLAB","DRREDDY","BPCL","IOC",
           "BHARTIARTL","TITAN","M&M","HEROMOTOCO","EICHERMOT","TATAMOTORS","COALINDIA","SHREECEM","HAVELLS","SIEMENS","TORNTPHARM",
           "PIDILITIND","LTIM","BEL","DLF","INDUSINDBK","PNB","BANKBARODA","CANBK","FEDERALBNK","IDFCFIRSTB","YESBANK","ZEEL","ZOMATO" ]

# =============================
# INDICATORS
# =============================
def add_indicators(df):
    df = df.copy()
    if len(df) < 50: return df
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-9)
    high_low = df['High'] - df['Low']
    tr = pd.concat([high_low, abs(df['High'] - df['Close'].shift()), abs(df['Low'] - df['Close'].shift())], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()
    df['VolAvg'] = df['Volume'].rolling(20).mean()
    return df

@st.cache_data(ttl=60)
def fetch_data(symbols, interval, period):
    tickers = [s + ".NS" for s in symbols]
    return yf.download(tickers, period=period, interval=interval, group_by='ticker', progress=False)

with st.spinner("🚀 Loading NSE 200 Data..."):
    data_5m = fetch_data(stocks, "5m", "5d")

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='BigMove_Report')
    return output.getvalue()

# =============================
# BIG MOVE TABLE
# =============================
if st.button("RUN BIG MOVE SCAN"):
    big_logs = []
    for s in stocks:
        try:
            df_raw = data_5m.get(s + ".NS")
            if df_raw is None or df_raw.empty: continue
            df = add_indicators(df_raw.dropna())
            l = df.iloc[-1]

            # BIG MOVE condition → Strong volume + Trend confirmation
            if l['Volume'] > l['VolAvg'] * 3:
                trend = "UP" if l['EMA20'] > l['EMA50'] else "DOWN"
                entry = round(l['Close'], 2)
                big_logs.append({
                    "TIME": df.index[-1].astimezone(IST).strftime('%H:%M'),
                    "STOCK": s,
                    "TREND": trend,
                    "ENTRY": entry,
                    "VWAP": round(l['VWAP'], 2),
                    "BIG PLAYER": "🔥 YES",
                    "SL": round(entry - (l['ATR']*2) if trend=="UP" else entry + (l['ATR']*2), 2),
                    "TGT": round(entry + (l['ATR']*4) if trend=="UP" else entry - (l['ATR']*4), 2)
                })
        except: continue

    if big_logs:
        big_df = pd.DataFrame(big_logs)
        st.dataframe(big_df, use_container_width=True)
        st.download_button("📥 Download BIG MOVE Excel", data=to_excel(big_df), file_name=f"BigMove_{now.strftime('%Y%m%d_%H%M')}.xlsx")
    else:
        st.warning("No BIG MOVE signals found right now.")
