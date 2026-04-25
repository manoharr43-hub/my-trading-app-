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
st.set_page_config(page_title="🔥 NSE AI PRO V12", layout="wide")
st.title("🚀 NSE AI PRO V12 (SECTOR + FILTER FINAL)")
st_autorefresh(interval=60000, key="refresh")

# =============================
# SESSION INIT
# =============================
if "live_big" not in st.session_state:
    st.session_state.live_big = []
if "strength" not in st.session_state:
    st.session_state.strength = pd.DataFrame()
if "bt_df" not in st.session_state:
    st.session_state.bt_df = pd.DataFrame()

# =============================
# SECTOR MAP
# =============================
sector_map = {
    "Banking": ["HDFCBANK","ICICIBANK","SBIN","AXISBANK","KOTAKBANK"],
    "IT": ["INFY","TCS","HCLTECH","WIPRO","TECHM"],
    "Pharma": ["SUNPHARMA","DRREDDY","CIPLA","DIVISLAB"],
    "Auto": ["MARUTI","M&M","TATAMOTORS","HEROMOTOCO","BAJAJ-AUTO"],
    "Metals": ["JSWSTEEL","TATASTEEL","HINDALCO","VEDL"],
    "FMCG": ["ITC","HINDUNILVR","NESTLEIND","BRITANNIA","DABUR"],
    "Oil & Gas": ["RELIANCE","ONGC","BPCL","IOC","GAIL"],
    "Infra": ["LT","ADANIPORTS","POWERGRID","NTPC"],
    "Telecom": ["BHARTIARTL","IDEA"]
}

selected_sector = st.sidebar.selectbox("📂 Select Sector", list(sector_map.keys()))
stocks = sector_map[selected_sector]

# =============================
# FUNCTIONS
# =============================
def clean_time(ts):
    return pd.to_datetime(ts).strftime("%I:%M %p").lstrip("0")

@st.cache_data(ttl=60)
def load_data(stock, period="1d"):
    df = yf.Ticker(stock + ".NS").history(period=period, interval="5m")
    if df.empty:
        return pd.DataFrame()
    return df.between_time("09:15","15:30")

def filter_alternate_signals(signals):
    if not signals:
        return []
    filtered = [signals[0]]
    for sig in signals[1:]:
        if sig["Type"] != filtered[-1]["Type"]:
            filtered.append(sig)
    return filtered

# =============================
# BIG PLAYER LOGIC
# =============================
def big_player(df, stock):
    if df.empty or len(df) < 30:
        return []
    df = df.copy()
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    df['VWAP'] = (df['Volume'] * (df['High']+df['Low']+df['Close'])/3).cumsum() / df['Volume'].cumsum()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    df['AvgVol'] = df['Volume'].rolling(20).mean()
    df['Body'] = abs(df['Close'] - df['Open'])
    df['Range'] = df['High'] - df['Low']
    df['StrongCandle'] = df['Body'] > (df['Range'] * 0.6)

    entries = []
    for i in range(25, len(df)):
        price = df['Close'].iloc[i]
        score = 0
        if price > df['EMA20'].iloc[i]: score += 1
        if price > df['EMA50'].iloc[i]: score += 1
        if price > df['VWAP'].iloc[i]: score += 1
        if df['RSI'].iloc[i] > 60: score += 1
        if df['Volume'].iloc[i] > df['AvgVol'].iloc[i]*3: score += 1
        confidence = f"{score}/5"

        if (df['Volume'].iloc[i] > df['AvgVol'].iloc[i]*2.5 and
            price > df['EMA20'].iloc[i] > df['EMA50'].iloc[i] and
            price > df['VWAP'].iloc[i] and
            df['RSI'].iloc[i] > 55 and
            df['StrongCandle'].iloc[i]):
            entries.append({"Stock": stock,"Type": "BIG BUY","Price": price,
                            "TimeRaw": df.index[i],"Time": clean_time(df.index[i]),
                            "Confidence": confidence})
        elif (df['Volume'].iloc[i] > df['AvgVol'].iloc[i]*2.5 and
              price < df['EMA20'].iloc[i] < df['EMA50'].iloc[i] and
              price < df['VWAP'].iloc[i] and
              df['RSI'].iloc[i] < 45 and
              df['StrongCandle'].iloc[i]):
            entries.append({"Stock": stock,"Type": "BIG SELL","Price": price,
                            "TimeRaw": df.index[i],"Time": clean_time(df.index[i]),
                            "Confidence": confidence})
    return entries[-5:] if entries else []

def strength_meter(df):
    if df.empty:
        return 0
    return round(((df['Close'].iloc[-1] / df['Close'].iloc[0]) - 1) * 100, 2)
