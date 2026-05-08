import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from concurrent.futures import ThreadPoolExecutor

# =========================
# APP CONFIG
# =========================
st.set_page_config(page_title="🚀 NSE AI V51 PRO - NIFTY200", layout="wide")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI V51 PRO - NIFTY 200 DECISION SYSTEM")
st.markdown(f"🕒 LIVE TIME: {now.strftime('%Y-%m-%d %H:%M:%S')}")

# =========================
# STOCK LIST
# =========================
stocks = [
    "RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","AXISBANK",
    "ITC","LT","BHARTIARTL","KOTAKBANK","HCLTECH","WIPRO","TECHM",
    "SUNPHARMA","TITAN","MARUTI","ONGC","NTPC","POWERGRID","COALINDIA",
    "BAJFINANCE","BAJAJFINSV","ADANIENT","ADANIPORTS","ULTRACEMCO",
    "ASIANPAINT","NESTLEIND","BRITANNIA","DRREDDY","CIPLA","DIVISLAB",
    "EICHERMOT","HEROMOTOCO","TATAMOTORS","M&M","TVSMOTOR",
    "JSWSTEEL","TATASTEEL","HINDALCO","GRASIM","UPL","PIDILITIND",
    "DABUR","MARICO","COLPAL","TRENT","PAGEIND","HAVELLS",
    "SIEMENS","ABB","HAL","BEL","BHEL","DLF","GAIL","IOC","BPCL",
    "INDUSINDBK","PNB","BANKBARODA","CANBK","SBILIFE","HDFCLIFE"
]

# =========================
# DATA LOAD (FIXED SAFE VERSION)
# =========================
@st.cache_data(ttl=300)
def load_data():
    tickers = [s + ".NS" for s in stocks]

    try:
        df = yf.download(
            tickers,
            period="1mo",
            interval="15m",
            group_by="ticker",
            threads=True
        )
        return df
    except Exception as e:
        st.error(f"Data load failed: {e}")
        return pd.DataFrame()

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
# SCORE ENGINE
# =========================
def score_engine(row):
    score = 0

    if row['Close'] > row['VWAP']:
        score += 25

    if 55 <= row['RSI'] <= 68:
        score += 25
    elif 30 <= row['RSI'] < 45:
        score += 25

    if row['Volume'] > row['VOL_AVG']:
        score += 20

    if row['Close'] > row['EMA21']:
        score += 20

    return min(score, 100)

# =========================
# WIN PROBABILITY
# =========================
def win_probability(score, rsi_val):
    base = score

    if 55 <= rsi_val <= 65:
        base += 10

    if base >= 90:
        return 85
    elif base >= 80:
        return 75
    elif base >= 70:
        return 65
    elif base >= 60:
        return 55
    else:
        return 40

# =========================
# ENGINE (FIXED SAFE VERSION)
# =========================
def engine(stock, raw, date):

    try:
        key = stock + ".NS"

        if key not in raw.columns.get_level_values(0):
            return []

        df = raw[key].dropna().copy()

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

        # timezone safe
        if df.index.tz is None:
            df.index = df.index.tz_localize("UTC")

        df.index = df.index.tz_convert(IST)

        df = df[df.index.date == pd.to_datetime(date).date()]

        results = []

        if df.empty:
            return []

        for i in range(1, len(df)):

            row = df.iloc[i]
            t = row.name.time()

            if not (datetime.strptime("09:30","%H:%M").time() <= t <= datetime.strptime("14:45","%H:%M").time()):
                continue

            vol_ok = row['Volume'] > row['VOL_AVG']

            buy = (row['Close'] > row['VWAP'] and 50 < row['RSI'] < 70 and vol_ok)
            sell = (row['Close'] < row['VWAP'] and 30 < row['RSI'] < 50 and vol_ok)

            if not (buy or sell):
                continue

            entry = row['Close']
            atr = row['ATR']

            if pd.isna(atr):
                continue

            sl = entry - atr * 2.5 if buy else entry + atr * 2.5
            tgt = entry + atr * 2.0 if buy else entry - atr * 2.0

            score = score_engine(row)
            win = win_probability(score, row['RSI'])

            decision = (
                "STRONG BUY" if score >= 80 else
                "BUY" if score >= 65 else
                "HOLD" if score >= 50 else
                "AVOID"
            )

            status = "OPEN"
            future = df.iloc[i+1:i+20]

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
                "TIME": row.name.strftime("%H:%M"),
                "STOCK": stock,
                "SIGNAL": "BUY" if buy else "SELL",
                "ENTRY": round(entry, 2),
                "SL": round(sl, 2),
                "TARGET": round(tgt, 2),
                "RSI": round(row['RSI'], 2),
                "SCORE": score,
                "WIN%": win,
                "DECISION": decision,
                "STATUS": status
            })

        return results

    except Exception:
        return []

# =========================
# UI
# =========================
tab1, tab2 = st.tabs(["🔥 LIVE SCANNER", "📊 BACKTEST"])

# =========================
# LIVE SCANNER
# =========================
with tab1:

    if st.button("RUN LIVE SCAN (NIFTY200)"):

        results = []

        with ThreadPoolExecutor(max_workers=12) as ex:
            futures = [ex.submit(engine, s, data, now.date()) for s in stocks]

            for f in futures:
                r = f.result()
                if r:
                    results.extend(r)

        df = pd.DataFrame(results)

        if not df.empty:
            df = df.sort_values("SCORE", ascending=False)

            st.subheader("🥇 TOP 5 PICKS")
            st.dataframe(df.head(5))

            st.subheader("📊 ALL SIGNALS")
            st.dataframe(df)
        else:
            st.warning("NO SIGNALS FOUND")

# =========================
# BACKTEST
# =========================
with tab2:

    d = st.date_input("Select Date", now.date() - timedelta(days=1))

    if st.button("RUN BACKTEST"):

        results = []

        with ThreadPoolExecutor(max_workers=12) as ex:
            futures = [ex.submit(engine, s, data, d) for s in stocks]

            for f in futures:
                r = f.result()
                if r:
                    results.extend(r)

        df = pd.DataFrame(results)

        if not df.empty:
            st.dataframe(df)

            wins = len(df[df['STATUS'] == "TARGET"])
            losses = len(df[df['STATUS'] == "SL"])

            st.success(f"WINS: {wins} | LOSSES: {losses}")
        else:
            st.warning("NO DATA")
