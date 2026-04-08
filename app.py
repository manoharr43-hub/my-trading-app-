import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="NSE Pro Scanner", layout="wide")
st_autorefresh(interval=15000, key="refresh")

# =============================
# INDICATORS
# =============================
def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def ema(series, span):
    return series.ewm(span=span, adjust=False).mean()

# =============================
# DATA FETCH
# =============================
@st.cache_data(ttl=20)
def get_data(stocks):
    return yf.download(stocks, period="5d", interval="5m", group_by="ticker", progress=False)

# =============================
# ANALYSIS
# =============================
def analyze_intraday(df, ticker):
    try:
        d = df[ticker].copy() if isinstance(df.columns, pd.MultiIndex) else df.copy()

        if d is None or len(d) < 20:
            return None

        # Only today
        d["Date"] = d.index.date
        today = d["Date"].iloc[-1]
        d = d[d["Date"] == today].copy()

        if len(d) < 10:
            return None

        close = d["Close"]
        high = d["High"]
        low = d["Low"]
        vol = d["Volume"]

        ltp = float(close.iloc[-1])

        # VWAP
        d["VWAP"] = (close * vol).cumsum() / vol.cumsum()

        # RSI
        d["RSI"] = rsi(close)

        # ORB
        orb_high = round(high.iloc[:6].max(), 2)
        orb_low = round(low.iloc[:6].min(), 2)

        # Support / Resistance
        pivot = (high.iloc[-2] + low.iloc[-2] + close.iloc[-2]) / 3
        resistance = round((2 * pivot) - low.iloc[-2], 2)
        support = round((2 * pivot) - high.iloc[-2], 2)

        # Trend
        d["EMA20"] = ema(close, 20)
        d["EMA50"] = ema(close, 50)

        trend = "SIDEWAYS"
        if d["EMA20"].iloc[-1] > d["EMA50"].iloc[-1]:
            trend = "UPTREND"
        elif d["EMA20"].iloc[-1] < d["EMA50"].iloc[-1]:
            trend = "DOWNTREND"

        # Signal (simple)
        signal = "WAIT"
        if ltp > d["VWAP"].iloc[-1
