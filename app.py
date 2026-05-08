import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from concurrent.futures import ThreadPoolExecutor
import io

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(page_title="🚀 NSE AI V29 PRO (200 STOCKS)", layout="wide")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

# =========================================================
# MARKET TREND
# =========================================================
def market_trend():
    try:
        n = yf.Ticker("^NSEI").history(period="5d")
        return n['Close'].iloc[-1] > n['Close'].rolling(5).mean().iloc[-1]
    except:
        return True

trend_up = market_trend()

# =========================================================
# NSE 200 STOCKS (EXPANDED LIST)
# =========================================================
nse_200 = [
    # NIFTY50 CORE
    "RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","AXISBANK","ITC",
    "LT","BHARTIARTL","KOTAKBANK","HCLTECH","WIPRO","TECHM","SUNPHARMA",
    "TITAN","MARUTI","ONGC","NTPC","POWERGRID","COALINDIA","JSWSTEEL",
    "TATASTEEL","HINDALCO","BAJFINANCE","BAJAJFINSV","ASIANPAINT",
    "ULTRACEMCO","NESTLEIND","BRITANNIA","DRREDDY","CIPLA","DIVISLAB",

    # MID CAP & HIGH VOLUME
    "ADANIENT","ADANIPORTS","ADANIGREEN","ADANIPOWER","BEL","BHEL","DLF",
    "GAIL","IOC","BPCL","HINDPETRO","M&M","HEROMOTOCO","EICHERMOT",
    "INDUSINDBK","IDFCFIRSTB","PNB","BANKBARODA","CANBK","UNIONBANK",
    "LICI","SBILIFE","ICICIPRULI","HDFCLIFE","TATAMOTORS","TATAPOWER",
    "TATAELXSI","LUPIN","ZYDUSLIFE","ABB","SIEMENS","HAL","VEDL","NMDC",

    # ADDITIONAL LIQUID STOCKS
    "GRASIM","UPL","PIDILITIND","DABUR","MARICO","COLPAL","TRENT",
    "PAGEIND","TATACONSUM","BERGEPAINT","ASHOKLEY","TVSMOTOR",
    "SAIL","JINDALSTEL","AMBUJACEM","ACC","JKCEMENT","RECLTD","PFC"
]

# =========================================================
# DATA FETCH
# =========================================================
@st.cache_data(ttl=300)
def fetch_data():
    return yf.download(
        [s + ".NS" for s in nse_200],
        period="1mo",
        interval="15m",
        group_by="ticker",
        auto_adjust=True,
        threads=True
    )

data = fetch_data()

# =========================================================
# RSI
# =========================================================
def rsi(x, p=14):
    d = x.diff()
    g = d.clip(lower=0)
    l = -d.clip(upper=0)
    rs = g.rolling(p).mean() / (l.rolling(p).mean() + 1e-9)
    return 100 - (100 / (1 + rs))

# =========================================================
# ENGINE
# =========================================================
def engine(stock, raw, date):

    try:
        df = raw[stock + ".NS"].dropna().copy()
        if len(df) < 60:
            return []

        # ================= INDICATORS =================
        df['EMA21'] = df['Close'].ewm(span=21).mean()
        df['EMA50'] = df['Close'].ewm(span=50).mean()

        df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-9)

        tr = pd.concat([
            df['High']-df['Low'],
            abs(df['High']-df['Close'].shift()),
            abs(df['Low']-df['Close'].shift())
        ], axis=1).max(axis=1)

        df['ATR'] = tr.rolling(14, min_periods=1).mean()

        df['RSI'] = rsi(df['Close'])

        df['VOL_AVG'] = df['Volume'].rolling(20).mean()

        # timezone
        if df.index.tz is None:
            df.index = df.index.tz_localize("UTC")

        df.index = df.index.tz_convert(IST)

        df = df[df.index.date == pd.to_datetime(date).date()]

        results = []

        for i in range(1, len(df)):

            row = df.iloc[i]
            prev = df.iloc[i-1]

            t = row.name.time()

            if not (datetime.strptime("09:30","%H:%M").time()
                    <= t <= datetime.strptime("14:45","%H:%M").time()):
                continue

            vol_ok = row['Volume'] > row['VOL_AVG']

            candle_ok = (row['High'] - row['Low']) < row['ATR'] * 1.3

            # ================= BUY =================
            buy = (
                row['Close'] > row['VWAP'] and
                row['EMA21'] > row['EMA50'] and
                55 < row['RSI'] < 70 and
                vol_ok and
                candle_ok and
                trend_up
            )

            # ================= SELL =================
            sell = (
                row['Close'] < row['VWAP'] and
                row['EMA21'] < row['EMA50'] and
                30 < row['RSI'] < 45 and
                vol_ok and
                not trend_up
            )

            if buy or sell:

                entry = row['Close']
                atr = row['ATR']

                if buy:
                    sl = entry - (atr * 1.8)
                    tgt = entry + (atr * 1.6)
                else:
                    sl = entry + (atr * 1.8)
                    tgt = entry - (atr * 1.6)

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
                    "ENTRY": round(entry,2),
                    "SL": round(sl,2),
                    "TARGET": round(tgt,2),
                    "RSI": round(row['RSI'],2),
                    "STATUS": status
                })

        return results

    except:
        return []

# =========================================================
# UI
# =========================================================
tab1, tab2 = st.tabs(["🔥 LIVE SCAN (200 STOCKS)", "📊 BACKTEST"])

# ================= LIVE =================
with tab1:

    if st.button("RUN LIVE SCAN"):

        results = []

        with ThreadPoolExecutor(max_workers=12) as ex:
            futures = [ex.submit(engine, s, data, now.date()) for s in nse_200]

            for f in futures:
                r = f.result()
                if r:
                    results.append(r[-1])

        if results:
            df = pd.DataFrame(results)
            st.dataframe(df)
        else:
            st.warning("NO SIGNALS FOUND")

# ================= BACKTEST =================
with tab2:

    d = st.date_input("Select Date", now.date()-timedelta(days=1))

    if st.button("RUN BACKTEST"):

        results = []

        with ThreadPoolExecutor(max_workers=12) as ex:
            futures = [ex.submit(engine, s, data, d) for s in nse_200]

            for f in futures:
                r = f.result()
                if r:
                    results.extend(r)

        if results:

            df = pd.DataFrame(results)

            st.dataframe(df)

            wins = len(df[df['STATUS']=="TARGET"])
            losses = len(df[df['STATUS']=="SL"])

            st.success(f"WINS: {wins} | LOSSES: {losses}")

        else:
            st.warning("NO DATA")
