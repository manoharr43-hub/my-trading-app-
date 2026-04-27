import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V22", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V22 - CLEAN SYSTEM")
st.write(f"🕒 Market Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")

# =============================
# STOCK LIST
# =============================
stocks = [
    "RELIANCE","TCS","HDFCBANK","ICICIBANK","INFY","BHARTIARTL",
    "SBIN","ITC","LT","BAJFINANCE","AXISBANK","KOTAKBANK",
    "HCLTECH","MARUTI","SUNPHARMA","TITAN","TATAMOTORS",
    "ULTRACEMCO","ADANIENT","JSWSTEEL"
]

# =============================
# INDICATORS (FIXED ATR)
# =============================
def add_indicators(df):
    df = df.copy()

    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-9)

    # ✅ TRUE ATR FIX
    high_low = df['High'] - df['Low']
    high_close = abs(df['High'] - df['Close'].shift())
    low_close = abs(df['Low'] - df['Close'].shift())

    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()

    return df

# =============================
# SAFE DATA FETCH
# =============================
@st.cache_data(ttl=60)
def fetch_data(symbols, interval, period):
    tickers = [s + ".NS" for s in symbols]
    try:
        data = yf.download(tickers, period=period, interval=interval, group_by='ticker', progress=False)
        return data
    except:
        return pd.DataFrame()

# =============================
# LOAD DATA
# =============================
data_5m = fetch_data(stocks, "5m", "5d")
data_1d = fetch_data(stocks, "1d", "6mo")

# =============================
# TABS
# =============================
tab1, tab2, tab3 = st.tabs([
    "🔍 1D SCANNER",
    "🎯 PULLBACK SCANNER",
    "🔥 BACKTEST"
])

# =============================
# TAB 1 - TREND SCANNER
# =============================
with tab1:
    if st.button("RUN SCAN"):
        results = []

        for s in stocks:
            try:
                df1 = data_1d.get(s + ".NS")
                df5 = data_5m.get(s + ".NS")

                if df1 is None or df5 is None:
                    continue

                df1 = add_indicators(df1.dropna())
                df5 = add_indicators(df5.dropna())

                last = df5.iloc[-1]

                trend_up = df1['Close'].iloc[-1] > df1['EMA20'].iloc[-1]

                if trend_up and last['Close'] > last['VWAP']:
                    results.append({
                        "STOCK": s,
                        "ENTRY": round(last['Close'], 2),
                        "SL": round(last['Close'] - last['ATR']*1.5, 2),
                        "TARGET": round(last['Close'] + last['ATR']*3, 2),
                        "VOLUME": "HIGH" if last['Volume'] > df5['Volume'].rolling(20).mean().iloc[-1]*2 else "NORMAL"
                    })

            except:
                continue

        st.dataframe(pd.DataFrame(results), use_container_width=True)

# =============================
# TAB 2 - PULLBACK SCANNER
# =============================
with tab2:
    if st.button("SCAN PULLBACK"):
        pb = []

        for s in stocks:
            try:
                df = data_5m.get(s + ".NS")
                if df is None:
                    continue

                df = add_indicators(df.dropna())
                last = df.iloc[-1]

                dist = abs(last['Close'] - last['EMA20']) / last['EMA20']

                if dist < 0.005 and last['Close'] > last['Open']:
                    pb.append({
                        "STOCK": s,
                        "ENTRY": round(last['Close'], 2),
                        "SL": round(last['Close'] - last['ATR'], 2),
                        "TARGET": round(last['Close'] + last['ATR']*2, 2)
                    })

            except:
                continue

        st.dataframe(pd.DataFrame(pb), use_container_width=True)

# =============================
# TAB 3 - BACKTEST FIXED
# =============================
with tab3:
    test_date = st.date_input("Select Date", value=now.date() - timedelta(days=1))

    if st.button("RUN BACKTEST"):
        logs = []

        for s in stocks:
            try:
                df = data_5m.get(s + ".NS")
                if df is None:
                    continue

                df = add_indicators(df.dropna())
                df_day = df[df.index.date == test_date]

                if df_day.empty:
                    continue

                for i in range(15, len(df_day)-5):
                    snap = df_day.iloc[:i+1]
                    last = snap.iloc[-1]

                    dist = abs(last['Close'] - last['EMA20']) / last['EMA20']

                    if dist < 0.005:
                        entry = last['Close']
                        atr = last['ATR']

                        future = df_day.iloc[i+1:i+6]

                        tp_hit = any(future['High'] > entry + atr*2)
                        sl_hit = any(future['Low'] < entry - atr)

                        if tp_hit:
                            result = "WIN ✅"
                        elif sl_hit:
                            result = "LOSS ❌"
                        else:
                            result = "NO TRADE ⚪"

                        logs.append({
                            "STOCK": s,
                            "ENTRY": round(entry,2),
                            "RESULT": result
                        })

            except:
                continue

        st.dataframe(pd.DataFrame(logs), use_container_width=True)
