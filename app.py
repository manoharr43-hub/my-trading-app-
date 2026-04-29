import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta, time
import pytz

# ==========================================
# CONFIG
# ==========================================
st.set_page_config(page_title="🚀 NSE AI PRO V57", layout="wide")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V57 - COMPLETE SYSTEM")
st.write(f"🕒 {now.strftime('%Y-%m-%d %H:%M:%S')}")

# ==========================================
# NSE 200 STOCKS
# ==========================================
stocks = [
"RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","BHARTIARTL","ITC","KOTAKBANK","LT",
"HINDUNILVR","ASIANPAINT","AXISBANK","MARUTI","SUNPHARMA","TITAN","ULTRACEMCO","WIPRO","NESTLEIND",
"POWERGRID","NTPC","BAJFINANCE","BAJAJFINSV","ONGC","ADANIENT","ADANIPORTS","JSWSTEEL","TATASTEEL",
"HCLTECH","TECHM","GRASIM","DIVISLAB","DRREDDY","CIPLA","BRITANNIA","EICHERMOT","HEROMOTOCO",
"TATAMOTORS","M&M","COALINDIA","BPCL","IOC","SHREECEM","HAVELLS","SIEMENS","DLF","PIDILITIND"
]

# ==========================================
# INDICATORS
# ==========================================
def add_indicators(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df['EMA20'] = df['Close'].ewm(span=20).mean()

    df['Support'] = df['Low'].rolling(20).min()
    df['Resistance'] = df['High'].rolling(20).max()

    tr = pd.concat([
        df['High'] - df['Low'],
        abs(df['High'] - df['Close'].shift()),
        abs(df['Low'] - df['Close'].shift())
    ], axis=1).max(axis=1)

    df['ATR'] = tr.rolling(14).mean()
    df['VolAvg'] = df['Volume'].rolling(20).mean()

    return df

# ==========================================
# SCREEN TIME FILTER
# ==========================================
def in_session(dt):
    t = dt.time()
    return time(9,15) <= t <= time(15,30)

# ==========================================
# BIG PLAYER (BONUS)
# ==========================================
def big_player(row):
    return row['Volume'] > row['VolAvg'] * 2

# ==========================================
# SIGNAL ENGINE
# ==========================================
def get_signal(row, prev):
    dist = abs(row['Close'] - row['EMA20']) / row['EMA20']

    # SUPPORT BUY
    if row['Close'] <= row['Support'] * 1.01:
        return "BUY SUPPORT"

    # RESISTANCE SELL
    if row['Close'] >= row['Resistance'] * 0.99:
        return "SELL RESISTANCE"

    # PULLBACK
    if dist < 0.012:
        return "BUY" if row['Close'] > row['EMA20'] else "SELL"

    # BREAKOUT
    if prev['Close'] < row['EMA20'] and row['Close'] > row['EMA20']:
        return "BUY"
    if prev['Close'] > row['EMA20'] and row['Close'] < row['EMA20']:
        return "SELL"

    return None

# ==========================================
# DATA
# ==========================================
@st.cache_data(ttl=120)
def get_data():
    return yf.download([s+".NS" for s in stocks],
                       period="5d", interval="5m", group_by="ticker")

data = get_data()

# ==========================================
# LIVE SCAN
# ==========================================
if st.button("🚀 SCAN NSE200"):
    results = []

    for s in stocks:
        try:
            df = data[s+".NS"].dropna()
            df = add_indicators(df)

            if len(df) < 30:
                continue

            row = df.iloc[-1]
            prev = df.iloc[-2]

            # SCREEN TIME
            if not in_session(df.index[-1].tz_convert(IST)):
                continue

            signal = get_signal(row, prev)
            if not signal:
                continue

            results.append({
                "STOCK": s,
                "SIGNAL": signal,
                "ENTRY": round(row['Close'],2),
                "SUPPORT": round(row['Support'],2),
                "RESISTANCE": round(row['Resistance'],2),
                "BIG PLAYER": "🔥 YES" if big_player(row) else "NO"
            })

        except:
            continue

    st.write(f"TOTAL SIGNALS: {len(results)}")
    st.dataframe(pd.DataFrame(results))

# ==========================================
# BACKTEST
# ==========================================
d = st.date_input("Select Date", now.date() - timedelta(days=1))

if st.button("RUN BACKTEST"):
    logs = []

    for s in stocks:
        try:
            df_all = data[s+".NS"].dropna()
            df_all.index = df_all.index.tz_convert(IST)

            df = add_indicators(df_all[df_all.index.date == d])

            for i in range(20, len(df)):
                row = df.iloc[i]
                prev = df.iloc[i-1]

                if not in_session(df.index[i]):
                    continue

                signal = get_signal(row, prev)
                if not signal:
                    continue

                logs.append({
                    "TIME": df.index[i].strftime('%H:%M'),
                    "STOCK": s,
                    "SIGNAL": signal,
                    "SUPPORT": round(row['Support'],2),
                    "RESISTANCE": round(row['Resistance'],2),
                    "BIG PLAYER": "🔥 YES" if big_player(row) else "NO"
                })

        except:
            continue

    st.write(f"BACKTEST SIGNALS: {len(logs)}")
    st.dataframe(pd.DataFrame(logs))
