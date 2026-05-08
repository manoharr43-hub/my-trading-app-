import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from concurrent.futures import ThreadPoolExecutor

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="🚀 NSE AI V52 PRO CLEAN", layout="wide")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI V52 PRO - CLEAN SYSTEM")
st.markdown(f"🕒 LIVE TIME: {now.strftime('%Y-%m-%d %H:%M:%S')}")

# =========================
# STOCK LIST (NIFTY200 CORE)
# =========================
stocks = [
    "RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","AXISBANK",
    "ITC","LT","BHARTIARTL","KOTAKBANK","HCLTECH","WIPRO","TECHM",
    "SUNPHARMA","TITAN","MARUTI","ONGC","NTPC","POWERGRID","COALINDIA",
    "BAJFINANCE","BAJAJFINSV","ADANIENT","ADANIPORTS","ULTRACEMCO",
    "ASIANPAINT","NESTLEIND","BRITANNIA","DRREDDY","CIPLA","DIVISLAB",
    "EICHERMOT","HEROMOTOCO","TATAMOTORS","M&M","TVSMOTOR",
    "JSWSTEEL","TATASTEEL","HINDALCO","GRASIM","UPL","PIDILITIND"
]

# =========================
# NIFTY50 FOR MARKET MOOD
# =========================
nifty50 = [
    "RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","AXISBANK",
    "ITC","LT","BHARTIARTL","KOTAKBANK","HCLTECH","WIPRO","TECHM",
    "SUNPHARMA","TITAN","MARUTI","ONGC","NTPC","POWERGRID","COALINDIA",
    "BAJFINANCE","ASIANPAINT","NESTLEIND","ULTRACEMPO","TATAMOTORS",
    "M&M","INDUSINDBK","HDFCLIFE","SBILIFE","ULTRACEMCO"
]

# =========================
# DATA LOAD
# =========================
@st.cache_data(ttl=300)
def load_data():
    return yf.download([s + ".NS" for s in stocks + nifty50],
                        period="1mo",
                        interval="15m",
                        group_by="ticker",
                        threads=True)

data = load_data()

# =========================
# RSI
# =========================
def rsi(x):
    d = x.diff()
    g = d.clip(lower=0)
    l = -d.clip(upper=0)
    rs = g.rolling(14).mean() / (l.rolling(14).mean() + 1e-9)
    return 100 - (100 / (1 + rs))

# =========================
# MARKET MOOD
# =========================
def market_mood():
    pos, neg = 0, 0

    for s in nifty50:
        key = s + ".NS"
        if key not in data.columns.get_level_values(0):
            continue

        df = data[key].dropna()
        if len(df) < 2:
            continue

        if df['Close'].iloc[-1] > df['Close'].iloc[-2]:
            pos += 1
        else:
            neg += 1

    return pos, neg

# =========================
# ENGINE
# =========================
def engine(stock):

    try:
        key = stock + ".NS"

        if key not in data.columns.get_level_values(0):
            return []

        df = data[key].dropna().copy()
        if len(df) < 60:
            return []

        df['EMA21'] = df['Close'].ewm(span=21).mean()
        df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-9)

        tr = pd.concat([
            df['High'] - df['Low'],
            abs(df['High'] - df['Close'].shift()),
            abs(df['Low'] - df['Close'].shift())
        ], axis=1).max(axis=1)

        df['ATR'] = tr.rolling(14).mean()
        df['RSI'] = rsi(df['Close'])
        df['VOL_AVG'] = df['Volume'].rolling(20).mean()

        df = df.dropna()

        results = []

        for i in range(1, len(df)):

            row = df.iloc[i]

            buy = row['Close'] > row['VWAP'] and row['RSI'] > 50 and row['Volume'] > row['VOL_AVG']
            sell = row['Close'] < row['VWAP'] and row['RSI'] < 50 and row['Volume'] > row['VOL_AVG']

            if not (buy or sell):
                continue

            entry = row['Close']
            atr = row['ATR']

            sl = entry - atr * 2.5 if buy else entry + atr * 2.5
            tgt = entry + atr * 2.0 if buy else entry - atr * 2.0

            status = "OPEN"

            future = df.iloc[i+1:i+15]

            for _, f in future.iterrows():
                if buy:
                    if f['High'] >= tgt:
                        status = "TARGET"
                        break
                    if f['Low'] <= sl:
                        status = "SL"
                        break
                else:
                    if f['Low'] <= tgt:
                        status = "TARGET"
                        break
                    if f['High'] >= sl:
                        status = "SL"
                        break

            results.append({
                "STOCK": stock,
                "SIGNAL": "BUY" if buy else "SELL",
                "ENTRY": round(entry, 2),
                "SL": round(sl, 2),
                "TARGET": round(tgt, 2),
                "RSI": round(row['RSI'], 2),
                "STATUS": status
            })

        return results

    except:
        return []

# =========================
# SCENARIO ANALYSIS
# =========================
def scenario(df):

    buy = df[df['SIGNAL'] == "BUY"]
    sell = df[df['SIGNAL'] == "SELL"]

    return (
        len(buy[buy['STATUS'] == "TARGET"]),
        len(buy[buy['STATUS'] == "SL"]),
        len(sell[sell['STATUS'] == "TARGET"]),
        len(sell[sell['STATUS'] == "SL"])
    )

# =========================
# EXCEL
# =========================
def to_csv(df):
    return df.to_csv(index=False).encode('utf-8')

# =========================
# UI
# =========================
tab1, tab2 = st.tabs(["🔥 LIVE", "📊 BACKTEST"])

# =========================
# LIVE
# =========================
with tab1:

    pos, neg = market_mood()

    col1, col2 = st.columns(2)

    col1.success(f"🟢 NIFTY50 POSITIVE: {pos}")
    col2.error(f"🔴 NIFTY50 NEGATIVE: {neg}")

    if st.button("RUN LIVE SCAN"):

        results = []

        with ThreadPoolExecutor(max_workers=10) as ex:
            for r in ex.map(engine, stocks):
                if r:
                    results.extend(r)

        df = pd.DataFrame(results)

        if not df.empty:

            st.subheader("📊 LIVE SIGNALS")
            st.dataframe(df)

            st.download_button("📥 DOWNLOAD LIVE EXCEL",
                               data=to_csv(df),
                               file_name="live_signals.csv")

# =========================
# BACKTEST
# =========================
with tab2:

    d = st.date_input("Select Date", now.date() - timedelta(days=1))

    if st.button("RUN BACKTEST"):

        results = []

        with ThreadPoolExecutor(max_workers=10) as ex:
            for r in ex.map(engine, stocks):
                if r:
                    results.extend(r)

        df = pd.DataFrame(results)

        if not df.empty:

            st.subheader("📊 BACKTEST RESULTS")
            st.dataframe(df)

            bw, bl, sw, sl = scenario(df)

            st.subheader("📊 SCENARIO ANALYSIS")
            st.success(f"BUY → WIN:{bw} LOSS:{bl}")
            st.warning(f"SELL → WIN:{sw} LOSS:{sl}")

            st.download_button("📥 DOWNLOAD BACKTEST EXCEL",
                               data=to_csv(df),
                               file_name="backtest.csv")

        else:
            st.warning("NO DATA FOUND")
