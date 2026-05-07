import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
from concurrent.futures import ThreadPoolExecutor
import io

# =========================================================
# 🚀 NSE AI QUANT PRO V9.0 SUPREME
# EMA9 + VWAP + MACD + RSI + RVOL + REAL BACKTEST
# =========================================================

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="🚀 NSE AI QUANT PRO V9.0 SUPREME",
    layout="wide"
)

# =========================================================
# TIMEZONE
# =========================================================
IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

# =========================================================
# CUSTOM CSS
# =========================================================
st.markdown("""
<style>

.main-title{
    text-align:center;
    font-size:42px;
    font-weight:bold;
    color:#22c55e;
}

.sub-title{
    text-align:center;
    font-size:18px;
    color:#cbd5e1;
    margin-bottom:25px;
}

.bull-box{
    background:#052e16;
    color:#22c55e;
    border:2px solid #22c55e;
    padding:18px;
    border-radius:12px;
    text-align:center;
    font-size:24px;
    font-weight:bold;
}

.bear-box{
    background:#450a0a;
    color:#f87171;
    border:2px solid #f87171;
    padding:18px;
    border-radius:12px;
    text-align:center;
    font-size:24px;
    font-weight:bold;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# HEADER
# =========================================================
st.markdown(
    '<div class="main-title">🚀 NSE AI QUANT PRO V9.0 SUPREME</div>',
    unsafe_allow_html=True
)

st.markdown(
    f'<div class="sub-title">🕒 LIVE TIME : {now.strftime("%H:%M:%S")} IST</div>',
    unsafe_allow_html=True
)

# =========================================================
# NSE STOCKS
# =========================================================
stocks = [
    "ABB","ACC","AUBANK","ADANIENT","ADANIPORTS",
    "APOLLOHOSP","ASHOKLEY","ASIANPAINT","AXISBANK",
    "BAJFINANCE","BAJAJFINSV","BANKBARODA","BEL",
    "BHARTIARTL","BHEL","BPCL","CANBK","CIPLA",
    "COALINDIA","DIXON","DLF","DRREDDY","EICHERMOT",
    "FEDERALBNK","GAIL","GRASIM","HAL","HAVELLS",
    "HCLTECH","HDFCBANK","HDFCLIFE","HINDALCO",
    "ICICIBANK","IDFCFIRSTB","INDUSINDBK","INFY",
    "IOC","IRCTC","ITC","JINDALSTEL","JSWSTEEL",
    "KOTAKBANK","LT","LTIM","M&M","MARUTI",
    "NTPC","ONGC","PFC","PNB","POWERGRID",
    "RECLTD","RELIANCE","SBIN","SUNPHARMA",
    "TATAMOTORS","TATASTEEL","TCS","TECHM",
    "TITAN","ULTRACEMCO","WIPRO","YESBANK",
    "ZOMATO"
]

# =========================================================
# INDICATORS
# =========================================================
def add_indicators(df):

    df = df.copy()

    if df.empty or len(df) < 50:
        return pd.DataFrame()

    # DATE
    df['DATE_ONLY'] = df.index.date

    # EMA
    df['EMA9'] = df['Close'].ewm(
        span=9,
        adjust=False
    ).mean()

    df['EMA20'] = df['Close'].ewm(
        span=20,
        adjust=False
    ).mean()

    # VWAP
    df['PV'] = df['Close'] * df['Volume']

    df['VWAP'] = (
        df.groupby('DATE_ONLY')['PV'].cumsum()
        /
        df.groupby('DATE_ONLY')['Volume'].cumsum()
    )

    # RSI
    delta = df['Close'].diff()

    gain = (
        delta.where(delta > 0, 0)
    ).rolling(14).mean()

    loss = (
        -delta.where(delta < 0, 0)
    ).rolling(14).mean()

    rs = gain / (loss + 1e-9)

    df['RSI'] = 100 - (100 / (1 + rs))

    # RVOL
    df['VOLAVG'] = df['Volume'].rolling(20).mean()

    df['RVOL'] = (
        df['Volume']
        /
        (df['VOLAVG'] + 1e-9)
    )

    # ATR
    tr1 = df['High'] - df['Low']
    tr2 = abs(df['High'] - df['Close'].shift())
    tr3 = abs(df['Low'] - df['Close'].shift())

    tr = pd.concat(
        [tr1, tr2, tr3],
        axis=1
    ).max(axis=1)

    df['ATR'] = tr.rolling(14).mean()

    # MACD
    ema12 = df['Close'].ewm(
        span=12,
        adjust=False
    ).mean()

    ema26 = df['Close'].ewm(
        span=26,
        adjust=False
    ).mean()

    df['MACD'] = ema12 - ema26

    df['MACD_SIGNAL'] = df['MACD'].ewm(
        span=9,
        adjust=False
    ).mean()

    return df

# =========================================================
# FETCH DATA
# =========================================================
@st.cache_data(ttl=60)
def fetch_data():

    tickers = [s + ".NS" for s in stocks]

    tickers.append("^NSEI")

    data_15m = yf.download(
        tickers=tickers,
        period="10d",
        interval="15m",
        auto_adjust=True,
        progress=False,
        threads=True,
        group_by="ticker"
    )

    nifty_1h = yf.download(
        "^NSEI",
        period="10d",
        interval="1h",
        auto_adjust=True,
        progress=False
    )

    return data_15m, nifty_1h

# =========================================================
# SCAN ENGINE
# =========================================================
def scan_stock(stock, data_15m, nifty_15m, market_trend, backtest=False):

    try:

        ticker = stock + ".NS"

        if ticker not in data_15m:
            return []

        raw = data_15m[ticker].dropna()

        df
