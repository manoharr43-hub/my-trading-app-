import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="NSE PRO INSTITUTIONAL SCANNER V11",
    page_icon="🚀",
    layout="wide"
)

# --------------------------------------------------
# DARK THEME CSS
# --------------------------------------------------
st.markdown("""
<style>
.stApp{background-color:#050816;color:white;}
h1,h2,h3,h4{color:white;}
[data-testid="stSidebar"]{background:#1d1f2b;}
.stButton>button{background:#0f62fe;color:white;border-radius:10px;height:50px;width:100%;font-weight:bold;}
.signal-box{background:#0f172a;padding:15px;border-radius:12px;border:1px solid #334155;}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# HEADER
# --------------------------------------------------
st.title("🚀 NSE PRO INSTITUTIONAL SCANNER V11")
st.caption(f"Live Time : {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}")

# --------------------------------------------------
# SIDEBAR SETTINGS
# --------------------------------------------------
st.sidebar.header("⚙ Scanner Settings")

timeframe = st.sidebar.selectbox("Timeframe", ["5m","15m","30m","1h","1d"], index=4)
period = st.sidebar.selectbox("Period", ["5d","1mo","3mo","6mo"], index=1)

min_ai_score = st.sidebar.slider("Minimum AI Score", 0, 100, 10)
min_rvol = st.sidebar.slider("Minimum RVOL", 0.5, 5.0, 1.0, 0.1)

# --------------------------------------------------
# NSE SYMBOLS
# --------------------------------------------------
NSE_SYMBOLS = [
    "RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","LT.NS","ITC.NS",
    "AXISBANK.NS","KOTAKBANK.NS","BAJFINANCE.NS","ASIANPAINT.NS","SUNPHARMA.NS","MARUTI.NS",
    "TITAN.NS","ULTRACEMCO.NS","WIPRO.NS","NTPC.NS","POWERGRID.NS","TATAMOTORS.NS",
    "HINDUNILVR.NS","BHARTIARTL.NS","ADANIGREEN.NS","ADANIPORTS.NS","GRASIM.NS","JSWSTEEL.NS",
    "ONGC.NS","COALINDIA.NS","DIVISLAB.NS","DRREDDY.NS","M&M.NS","HEROMOTOCO.NS","BRITANNIA.NS"
]

# --------------------------------------------------
# INDICATOR FUNCTIONS
# --------------------------------------------------
def calculate_rsi(df, period=14):
    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss
