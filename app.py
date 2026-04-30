import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta, time
import pytz
from streamlit_autorefresh import st_autorefresh

# ==========================================
# CONFIG
# ==========================================
st.set_page_config(page_title="🚀 NSE AI PRO V69 ULTRA PRO", layout="wide")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V69 ULTRA PRO")
st.write(f"🕒 {now.strftime('%Y-%m-%d %H:%M:%S')}")

st_autorefresh(interval=60000, key="refresh")

# Session
if "logs" not in st.session_state:
    st.session_state.logs = []

if "cooldown" not in st.session_state:
    st.session_state.cooldown = {}

# ==========================================
# STOCK LIST (SHORT SAMPLE – YOU CAN KEEP 200)
# ==========================================
nse_200 = ["RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","ITC","LT"]
tickers = [s + ".NS" for s in nse_200]

# ==========================================
# DATA
# ==========================================
@st.cache_data(ttl=300)
def get_data():
    return yf.download(tickers, period="15d", interval="5m", group_by="ticker", threads=True)

# ==========================================
# INDICATORS
# ==========================================
def indicators(df):
    df = df.copy()
    df["EMA20"] = df["Close"].ewm(span=20).mean()
    df["EMA50"] = df["Close"].ewm(span=50).mean()
    df["VOLAVG"] = df["Volume"].rolling(20).mean()

    delta = df["Close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))

    return df

# ==========================================
# SIGNAL ENGINE
# ==========================================
def signal_engine(row):
    sig, entry, sl, target, typ = None, None, None, None, None

    # 🔹 PULLBACK BUY
    if row["Close"] > row["EMA20"] and row["Low"] <= row["EMA20"]:
        if row["EMA20"] > row["EMA50"] and row["RSI"] < 65:
            sig = "BUY"
            typ = "PULLBACK"
            entry = row["Close"]
            sl = row["EMA20"] * 0.995
            target = entry + (entry - sl) * 2

    # 🔹 PULLBACK SELL
    elif row["Close"] < row["EMA20"] and row["High"] >= row["EMA20"]:
        if row["EMA20"] < row["EMA50"] and row["RSI"] > 35:
            sig = "SELL"
            typ = "PULLBACK"
            entry = row["Close"]
            sl = row["EMA20"] * 1.005
            target = entry - (sl - entry) * 2

    # 🔥 BIG PLAYER ENTRY
    if row["Volume"] > row["VOLAVG"] * 2:
        if row["Close"] > row["EMA20"]:
            sig = "BUY"
            typ = "BIG PLAYER"
            entry = row["Close"]
            sl = row["Low"]
            target = entry + (entry - sl) * 2.5

        elif row["Close"] < row["EMA20"]:
            sig = "SELL"
            typ = "BIG PLAYER"
            entry = row["Close"]
            sl = row["High"]
            target = entry - (sl - entry) * 2.5

    return sig, entry, sl, target, typ

# ==========================================
# AI SCORE
# ==========================================
def ai_score(row):
    score = 0

    if row["Close"] > row["EMA20"]:
        score += 2

    if row["Volume"] > row["VOLAVG"] * 1.5:
        score += 2

    if 40 < row["RSI"] < 60:
        score += 2

    return score

# ==========================================
# MARKET TIME
# ==========================================
def is_market_open(ts):
    return time(9, 15) <= ts.time() <= time(15, 30)

# ==========================================
# UI
# ==========================================
tab1, tab2 = st.tabs(["🚀 LIVE", "📊 BACKTEST"])

# ==========================================
# LIVE
# ==========================================
with tab1:
    if st.button("RUN SCANNER"):
        data = get_data()

        for s in nse_200:
            t = s + ".NS"
            if t not in data.columns.levels[0]:
                continue

            df = data[t].dropna()
            if len(df) < 50:
                continue

            df = indicators(df)

            row = df.iloc[-1]
            ts = df.index[-1].tz_convert(IST)

            if not is_market_open(ts):
                continue

            sig, entry, sl
