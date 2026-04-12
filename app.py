import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from streamlit_autorefresh import st_autorefresh

# =============================
# PAGE CONFIG + AUTO REFRESH
# =============================
st.set_page_config(page_title="🔥 NSE AI Scanner (Big Movers + Big Player)", layout="wide")
st_autorefresh(interval=60000, key="refresh")  # safer refresh (1 min)

# =============================
# NSE SECTORS
# =============================
sectors = {
    "Nifty 50": ["RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS"],
    "Banking": ["SBIN.NS","HDFCBANK.NS","ICICIBANK.NS","AXISBANK.NS","KOTAKBANK.NS","PNB.NS"],
    "IT": ["INFY.NS","TCS.NS","WIPRO.NS","HCLTECH.NS","TECHM.NS"],
    "Auto": ["MARUTI.NS","M&M.NS","BAJAJ-AUTO.NS","HEROMOTOCO.NS"],  # removed TATAMOTORS.NS
    "Pharma": ["SUNPHARMA.NS","DRREDDY.NS","CIPLA.NS","DIVISLAB.NS"],
    "FMCG": ["HINDUNILVR.NS","ITC.NS","NESTLEIND.NS","BRITANNIA.NS"],
    "Energy": ["RELIANCE.NS","ONGC.NS","BPCL.NS","IOC.NS"],
    "Metal": ["TATASTEEL.NS","JSWSTEEL.NS","HINDALCO.NS","COALINDIA.NS"]
}

# =============================
# SIDEBAR
# =============================
with st.sidebar:
    st.header("📊 Select NSE Sector")
    sector_name = st.selectbox("Sector", list(sectors.keys()))
    st.header("📌 Top 10 Big Movers")
    show_big = st.checkbox("Show Top 10 Movers Across All Sectors")
    st.header("🔎 Manual Symbol Entry")
    manual_symbol = st.text_input("Enter NSE Symbol (use .NS)", "")

# =============================
# COLOR FUNCTIONS
# =============================
def color_signal(val):
    if "BUY" in str(val):
        return "background-color: green; color: white"
    elif "SELL" in str(val):
        return "background-color: red; color: white"
    elif "Big Buyer" in str(val):
        return "background-color: orange; color: white"
    elif "Big Seller" in str(val):
        return "background-color: purple; color: white"
    return ""

def color_trend(val):
    if val == "UP":
        return "background-color: green; color: white"
    elif val == "DOWN":
        return "background-color: red; color: white"
    return ""

# =============================
# AI ANALYSIS FUNCTION
# =============================
def analyze(df):
    if df is None or len(df)<40:
        return None
    df = df.copy()
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    df['VWAP'] = (df['Close']*df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-9)
    delta = df['Close'].diff()
    gain = (delta.where(delta>0,0)).rolling(14).mean()
    loss = (-delta.where(delta<0,0)).rolling(14).mean()
    rs = gain / (loss + 1e-9)
