import streamlit as st import yfinance as yf import pandas as pd import numpy as np from streamlit_autorefresh import st_autorefresh

=============================

CONFIG

=============================

st.set_page_config(page_title="NSE Pro Scanner", layout="wide") st_autorefresh(interval=10000, key="refresh")

=============================

INDICATORS

=============================

def rsi(series, period=14): delta = series.diff() gain = delta.clip(lower=0).rolling(period).mean() loss = -delta.clip(upper=0).rolling(period).mean() rs = gain / loss return 100 - (100 / (1 + rs))

def ema(series, span): return series.ewm(span=span, adjust=False).mean()

=============================

DATA FETCH

=============================

@st.cache_data(ttl=20) def get_data(stocks): return yf.download(stocks, period="5d", interval="5m", group_by="ticker", progress=False)

=============================

LOGIC

=============================

def analyze(df, ticker): try: d = df[ticker] if isinstance(df.columns, pd.MultiIndex) else df if len(d) < 30: return None

close = d['Close']
    high = d['High']
    low = d['Low']
    vol = d['Volume']

    ltp = close.iloc[-1]

    d['VWAP'] = (close * vol).cumsum() / vol.cumsum()
    d['RSI'] = rsi(close)
    d['EMA20'] = ema(close, 20)
    d['EMA50'] = ema(close, 50)

    # Pivot
    pivot = (high.iloc[-2] + low.iloc[-2] + close.iloc[-2]) / 3
    res = (2 * pivot) - low.iloc[-2]
    sup = (2 * pivot) - high.iloc[-2]

    # Volume Spike
    avg_vol = vol.rolling(20).mean().iloc[-1]
    vol_spike = vol.iloc[-1] > avg_vol * 1.5

    signal = "WAIT"
    color = "#ffffff"

    if ltp > res and ltp > d['VWAP'].iloc[-1] and d['RSI'].iloc[-1] > 55 and vol_spike:
        signal = "STRONG BUY"
        color = "#d4edda"
    elif ltp < sup and ltp < d['VWAP'].iloc[-1] and d['RSI'].iloc[-1] < 45 and vol_spike:
        signal = "STRONG SELL"
        color = "#f8d7da"

    return {
        "Stock": ticker.replace(".NS", ""),
        "LTP": round(ltp, 2),
        "VWAP": round(d['VWAP'].iloc[-1], 2),
        "RSI": round(d['RSI'].iloc[-1], 1),
        "EMA20": round(d['EMA20'].iloc[-1], 2),
        "EMA50": round(d['EMA50'].iloc[-1], 2),
        "Signal": signal,
        "Volume Spike": "YES" if vol_spike else "NO
