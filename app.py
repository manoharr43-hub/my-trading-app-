import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V8 FINAL", layout="wide")
st_autorefresh(interval=60000, key="refresh")

st.title("🚀 MANOHAR NSE AI PRO V8 - FINAL STABLE TERMINAL")
st.markdown("---")

# =============================
# DATA LOADER (SAFE)
# =============================
@st.cache_data(ttl=60)
def load_stock(symbol):
    try:
        df = yf.download(symbol + ".NS", period="5d", interval="15m", progress=False)
        return df
    except:
        return None

# =============================
# SECTORS (FULL SAFE CLEAN - NO BROKEN STRINGS)
# =============================
sectors = {
    "NIFTY 50": [
        "RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK",
        "SBIN","ITC","LT","AXISBANK","BHARTIARTL"
    ],

    "BANKING": [
        "SBIN","HDFCBANK","ICICIBANK","AXISBANK","KOTAKBANK",
        "PNB","BANKBARODA","CANBK","FEDERALBNK"
    ],

    "AUTO": [
        "TATAMOTORS","MARUTI","M&M","HEROMOTOCO",
        "EICHERMOT","ASHOKLEY","TVSMOTOR","BAJAJ-AUTO"
    ],

    "METAL": [
        "TATASTEEL","JSWSTEEL","HINDALCO","JINDALSTEL",
        "SAIL","NATIONALUM","VEDL"
    ],

    "IT": [
        "TCS","INFY","WIPRO","HCLTECH","TECHM",
        "LTIM","COFORGE","MPHASIS"
    ],

    "PHARMA": [
        "SUNPHARMA","DRREDDY","CIPLA","DIVISLAB",
        "APOLLOHOSP","BIOCON","LUPIN"
    ],

    "OIL & GAS": [
        "RELIANCE","ONGC","IOC","BPCL","GAIL"
    ],

    "ENERGY": [
        "ADANIGREEN","ADANIPOWER","NTPC","POWERGRID","TATAPOWER"
    ],

    "INFRA": [
        "LT","IRB","NBCC","DLF","GMRINFRA"
    ],

    "CHEMICALS": [
        "PIDILITIND","DEEPAKNTR","UPL","ATUL","AARTIIND"
    ]
}

# =============================
# ANALYSIS ENGINE (SAFE)
# =============================
def analyze(df):

    if df is None or len(df) < 20:
        return None

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    vol = df["Volume"]

    e20 = close.ewm(span=20).mean()
    e50 = close.ewm(span=50).mean()

    price = float(close.iloc[-1])
    e20_v = float(e20.iloc[-1])
    e50_v = float(e50.iloc[-1])

    avg_vol = vol.rolling(20).mean().iloc[-1]
    curr_vol = vol.iloc[-1]

    if
