import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="NSE AI PRO V23", layout="wide")
st.title("🚀 NSE AI PRO V23 - Multi TF Smart System")

st_autorefresh(interval=60000, key="refresh")

# =============================
# STOCKS
# =============================
stocks = ["HDFCBANK","ICICIBANK","SBIN","RELIANCE","INFY","TCS"]

sl_pct = st.sidebar.slider("Stop Loss %", 0.5, 5.0, 1.0) / 100
tgt_pct = st.sidebar.slider("Target %", 1.0, 10.0, 2.0) / 100

# =============================
# DATA
# =============================
@st.cache_data(ttl=60)
def load(stock, interval):
    try:
        df = yf.Ticker(stock + ".NS").history(period="5d", interval=interval)
        return df.tz_localize(None)
    except:
        return pd.DataFrame()

# =============================
# INDICATORS
# =============================
def add_indicators(df):
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    tp = (df['High'] + df['Low'] + df['Close']) / 3
    df['VWAP'] = (tp
