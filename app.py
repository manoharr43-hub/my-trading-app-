import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V8 SECTOR+", layout="wide")
st_autorefresh(interval=60000, key="refresh")

st.title("🚀 NSE AI PRO V8 - MULTI SECTOR TERMINAL")
st.markdown("---")

# =============================
# DATA LOADER
# =============================
@st.cache_data(ttl=60)
def get_data(symbol):
    try:
        return yf.download(symbol + ".NS", period="5d", interval="15m", progress=False)
    except:
        return None

# =============================
# SECTORS (EXPANDED)
# =============================
sectors = {
    "📊 Nifty 50": [
        "RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK",
        "SBIN","ITC","LT","AXISBANK","BHARTIARTL"
    ],

    "🏦 Banking": [
        "SBIN","HDFCBANK","ICICIBANK","AXISBANK","KOTAKBANK",
        "PNB","BANKBARODA","CANBK","FEDERALBNK"
    ],

    "🚗 Auto": [
        "TATAMOTORS","MARUTI","M&M","HEROMOTOCO",
        "EICHERMOT","ASHOKLEY","TVSMOTOR","BAJAJ-AUTO"
    ],

    "⚙️ Metal": [
        "TATASTEEL","JSWSTEEL","HINDALCO","JINDALSTEL",
        "SAIL","NATIONALUM","VEDL"
    ],

    "💻 IT Sector": [
        "TCS","INFY","WIPRO","HCLTECH","TECHM",
        "LTIM","COFORGE","MPHASIS"
    ],

    "💊 Pharma": [
        "SUNPHARMA","DRREDDY","CIPLA","DIVISLAB",
        "APOLLOHOSP","BIOCON","LUPIN"
    ],

    "🛢️ Oil & Gas": [
        "RELIANCE","ONGC","IOC","BPCL","GAIL"
    ],

    "⚡ Energy": [
        "ADANIGREEN","ADANIPOWER","NTPC","POWERGRID","TATAPOWER"
    ],

    "🏗️ Infra": [
        "LT","IRB","NBCC","DLF","GMRINFRA"
    ],

    "🧪 Chemicals": [
        "PIDILITIND","DEEPAKNTR","UPL","AT
