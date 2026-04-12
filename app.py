import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from streamlit_autorefresh import st_autorefresh

# =============================
# PAGE CONFIG
# =============================
st.set_page_config(page_title="⚡ NSE Intraday AI Scanner (Final Safe)", layout="wide")
st_autorefresh(interval=15000, key="refresh")

# =============================
# NSE SECTORS
# =============================
sectors = {
    "Nifty 50": ["RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS"],
    "Banking": ["SBIN.NS","HDFCBANK.NS","ICICIBANK.NS","AXISBANK.NS","KOTAKBANK.NS"],
    "IT": ["INFY.NS","TCS.NS","WIPRO.NS","HCLTECH.NS","TECHM.NS"],
    "Auto": ["MARUTI.NS","M&M.NS","BAJAJ-AUTO.NS"],  # removed TATAMOTORS.NS
    "Pharma": ["SUNPHARMA.NS","DRREDDY.NS","CIPLA.NS"],
    "FMCG": ["HINDUNILVR.NS","ITC.NS","NESTLEIND.NS"],
    "Energy": ["RELIANCE.NS","ONGC.NS","BPCL.NS"],
    "Metal": ["TATASTEEL.NS","JSWSTEEL.NS","HINDALCO.NS"]
}

# =============================
# ANALYSIS FUNCTION
# =============================
def analyze_intraday(df):
    if df is None or len(df) < 30:
        return None
    df = df.copy()
    df['EMA9'] = df['Close'].ewm(span=9).mean()
    df['EMA21'] = df['Close'].ewm(span=21).mean()
    delta = df
