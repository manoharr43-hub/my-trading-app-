import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta, time as dtime
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
import os

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V30.5 HQ", layout="wide")
st.title("🚀 NSE AI PRO V30.5 HQ - SESSION UPGRADE")

st_autorefresh(interval=180000, key="refresh")

# =============================
# SECTORS
# =============================
sector_map = {
    "Banking": ["HDFCBANK","ICICIBANK","SBIN","AXISBANK","KOTAKBANK"],
    "IT": ["INFY","TCS","HCLTECH","WIPRO","TECHM"],
    "Auto": ["MARUTI","M&M","TATAMOTORS","HEROMOTOCO"],
    "Energy": ["RELIANCE","ONGC","IOC"],
    "Metals": ["TATASTEEL","HINDALCO"],
    "FMCG": ["ITC","HINDUNILVR"]
}

st.sidebar.header("⚙️ SETTINGS")
sector = st.sidebar.selectbox("Sector", list(sector_map.keys()))
stocks = sector_map[sector]

timeframe = st.sidebar.selectbox("Timeframe", ["5m","15m","30m","1h"])

sl_pct = st.sidebar.slider("SL %",0.5,5.0,1.0)/100
tgt_pct = st.sidebar.slider("Target %",1.0,10.0,2.0)/100

# =============================
# DATA LOADER
# =============================
@st.cache_data(ttl=120)
def load_data(stock):
    try:
        period = "7d" if timeframe=="5m" else "60d" if timeframe=="15m" else "2mo"
        df = yf.download(stock+".NS", period=period, interval=timeframe, progress=False)

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df.index = pd.to_datetime(df.index)

        if df.index.tz is not None:
            df.index = df.index.tz_convert(None)

        return df.dropna()
    except:
        return pd.DataFrame()

# =============================
# MARKET SESSION FILTER (9:15 - 3:30)
# =============================
def session_filter(df):
    df = df.copy()
    df.index = pd.to_datetime(df.index)
    if df.index.tz is not None:
        df.index = df.index.tz_convert(None)
    start = dtime(9, 15)
    end = dtime(15, 30)
    return df[(df.index.time >= start) & (df.index.time <= end)]

# =============================
# INDICATORS
# =============================
def indicators(df):
    df = df.copy()
    df["EMA20"] = df["Close"].ewm(span=20).mean()
    df["EMA50"] = df["Close"].
