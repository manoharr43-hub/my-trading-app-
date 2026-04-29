import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz, io
from streamlit_autorefresh import st_autorefresh

# ==========================================
# CONFIG
# ==========================================
st.set_page_config(page_title="🚀 NSE AI PRO V50", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V50 - ADAPTIVE SYSTEM")
st.write(f"🕒 {now.strftime('%Y-%m-%d %H:%M:%S')}")

stocks = ["RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","ITC","LT"]

# ==========================================
# INDICATORS
# ==========================================
def add_indicators(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    df['Date'] = df.index.date
    df['VWAP'] = df.groupby('Date').apply(
        lambda x: (x['Close']*x['Volume']).cumsum() / x['Volume'].cumsum()
    ).reset_index(level=0, drop=True)

    tr = pd.concat([
        df['High'] - df['Low'],
        abs(df['High'] - df['Close'].shift()),
        abs(df['Low'] - df['Close'].shift())
    ], axis=1).max(axis=1)

    df['ATR'] = tr.rolling(14).mean()
    df['VolAvg'] = df['Volume'].rolling(20).mean()

    return df

# ==========================================
# MARKET MODE (Adaptive)
# ==========================================
@st.cache_data(ttl=60)
def get_market_mode():
    try:
        nifty = yf.download("^NSEI", period="1d", interval="5m")

        if isinstance(nifty.columns, pd.MultiIndex):
            nifty.columns = nifty.columns.get_level_values(0)

        if len(nifty) < 20:
            return "SLOW"

        nifty['EMA20'] = nifty['Close'].ewm(span=20).mean()

        move = abs(nifty['Close'].iloc[-1] - nifty['Close'].iloc[-5])

        if move > nifty['Close'].iloc[-1] * 0.005:
            return "TRENDING"
        else:
            return "SLOW"

    except:
        return "SLOW"

# ==========================================
# PULLBACK
# ==========================================
def get_pullback(row, prev, mode):
    dist = abs(row['Close'] - row['EMA20']) / row['EMA20']

    limit = 0.004 if mode == "TRENDING" else 0.01

    if (dist < limit and row['Close'] > row['EMA20'] and
        row['Close'] > row['VWAP']):
        return "BUY"

    if (dist < limit and row['Close'] < row['EMA20'] and
        row['Close'] < row['VWAP']):
        return "SELL"

    return None

# ==========================================
# SCORE
# ==========================================
def score_trade(row, mode):
    score = 0

    if row['Volume'] > row['VolAvg'] * 2:
        score += 1

    if row['ATR'] > row['Close'] * 0.002:
        score += 1

    if mode == "TRENDING":
        return score >= 2
    else:
        return score >= 1

# ==========================================
# DATA
# ==========================================
@st.cache_data(ttl=60)
def get_data():
    return yf.download([s+".NS" for s in stocks],
                       period="5d", interval="5m", group_by="ticker")

def to_excel(df):
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    return buf.getvalue()

# ==========================================
# UI
# ==========================================
mode = get_market_mode()
st.write(f"📊 Market Mode: {mode}")

data = get_data()

if st.button("🚀 SCAN MARKET"):
    results = []

    for s in stocks:
        try:
            df = data[s+".NS"].dropna()
            df = add_indicators(df)

            row = df.iloc[-1]
            prev = df.iloc[-2]

            signal = get_pullback(row, prev, mode)
            if not signal:
                continue

            if not score_trade(row, mode):
                continue

            entry = round(row['Close'], 2)

            results.append({
                "TIME": df.index[-1].tz_convert(IST).strftime('%H:%M'),
                "STOCK": s,
                "SIGNAL": signal,
                "ENTRY": entry,
                "SL": round(entry - row['ATR']*1.5 if signal=="BUY" else entry + row['ATR']*1.5, 2),
                "TGT": round(entry + row['ATR']*3 if signal=="BUY" else entry - row['ATR']*3, 2),
                "MODE": mode
            })

        except:
            continue

    if results:
        df_out = pd.DataFrame(results)
        st.dataframe(df_out, use_container_width=True)
        st.download_button("📥 Download", to_excel(df_out), "signals_v50.xlsx")
    else:
        st.warning("No signals (market slow or strict filters)")
