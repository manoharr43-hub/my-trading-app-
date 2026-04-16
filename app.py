import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V8 FINAL", layout="wide")
st_autorefresh(interval=60000, key="refresh")

st.title("🚀 MANOHAR NSE AI PRO V8 FINAL TERMINAL")
st.markdown("---")

# =============================
# SAFE DATA LOADER
# =============================
@st.cache_data(ttl=60)
def load_stock(symbol):
    try:
        df = yf.download(symbol + ".NS", period="5d", interval="15m", progress=False)
        return df
    except:
        return None

# =============================
# SECTORS (FULL SAFE LIST)
# =============================
sectors = {
    "📊 NIFTY 50": [
        "RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK",
        "SBIN","ITC","LT","AXISBANK","BHARTIARTL"
    ],

    "🏦 BANKING": [
        "SBIN","HDFCBANK","ICICIBANK","AXISBANK","KOTAKBANK",
        "PNB","BANKBARODA","CANBK","FEDERALBNK"
    ],

    "🚗 AUTO": [
        "TATAMOTORS","MARUTI","M&M","HEROMOTOCO",
        "EICHERMOT","ASHOKLEY","TVSMOTOR","BAJAJ-AUTO"
    ],

    "⚙️ METAL": [
        "TATASTEEL","JSWSTEEL","HINDALCO","JINDALSTEL",
        "SAIL","NATIONALUM","VEDL"
    ],

    "💻 IT": [
        "TCS","INFY","WIPRO","HCLTECH","TECHM",
        "LTIM","COFORGE","MPHASIS"
    ],

    "💊 PHARMA": [
        "SUNPHARMA","DRREDDY","CIPLA","DIVISLAB",
        "APOLLOHOSP","BIOCON","LUPIN"
    ],

    "🛢️ OIL & GAS": [
        "RELIANCE","ONGC","IOC","BPCL","GAIL"
    ],

    "⚡ ENERGY
