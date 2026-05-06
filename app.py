import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🚀 NSE AI PRO V120 FIXED", layout="wide")

IST = pytz.timezone("Asia/Kolkata")
st.title("🚀 NSE AI PRO V120 FIXED")
st.write(datetime.now(IST).strftime("%d-%b-%Y %H:%M:%S"))

# =============================
# NSE 200 (Reduced for stability test)
# =============================
stocks = ["RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","ITC","LT","AXISBANK","KOTAKBANK"]

# =============================
# INDICATORS
# =============================
def add_indicators(df):
    df = df.copy()

    if df.empty or len(df) < 20:
        return None

    df['EMA20'] = df['Close'].ewm(span=20).mean()

    df['PV'] = df['Close'] * df['Volume']
    df['Date'] = df.index.date
    df['VWAP'] = df.groupby('Date')['PV'].cumsum() / df.groupby('Date')['Volume'].cumsum()

    tr = pd.concat([
        df['High']-df['Low'],
        abs(df['High']-df['Close'].shift()),
        abs(df['Low']-df['Close'].shift())
    ], axis=1).max(axis=1)

    df['ATR'] = tr.rolling(14).mean()

    delta = df['Close'].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()

    df['RSI'] = 100 - (100/(1+(gain/(loss+1e-9))))

    df['VolAvg'] = df['Volume'].rolling(20).mean()
    df['RVOL'] = df['Volume']/(df['VolAvg']+1e-9)

    return df

# =============================
# SINGLE STOCK FETCH (FIXED)
# =============================
@st.cache_data(ttl=60)
def fetch_stock(symbol):
    try:
        df = yf.download(symbol + ".NS", period="5d", interval="5m", progress=False)
        return df
    except:
        return pd.DataFrame()

# =============================
# SCANNER (SAFE VERSION)
# =============================
def scan(symbol):
    try:
        df = fetch_stock(symbol)
        df = add_indicators(df)

        if df is None or len(df) < 30:
            return None

        last = df.iloc[-1]

        # Basic logic (stable)
        if last['Close'] > last['VWAP'] and last['RSI'] > 55:
            signal = "BUY"
        elif last['Close'] < last['VWAP'] and last['RSI'] < 45:
            signal = "SELL"
        else:
            return None

        entry = round(last['Close'],2)
        sl = round(entry - last['ATR']*1.5,2)
        tgt = round(entry + last['ATR']*2.5,2)

        return {
            "STOCK": symbol,
            "SIGNAL": signal,
            "PRICE": entry,
            "SL": sl,
            "TARGET": tgt
        }

    except Exception as e:
        return None

# =============================
# UI
# =============================
if st.button("🚀 RUN SCANNER"):
    results = []

    for s in stocks:
        r = scan(s)
        if r:
            results.append(r)

    if results:
        df = pd.DataFrame(results)
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("No signals / Data issue")
