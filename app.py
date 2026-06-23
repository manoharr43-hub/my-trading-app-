# ==========================================
# NSE AI PRO V12 Institutional Edition
# Total Clean Code Generation
# ==========================================

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import io
import requests
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from xgboost import XGBClassifier
except:
    XGBClassifier = None

warnings.filterwarnings("ignore")

# ==========================================
# STREAMLIT CONFIG
# ==========================================
st.set_page_config(page_title="NSE AI PRO V12 Institutional", layout="wide", page_icon="🚀")
st.markdown("""<style>.stApp {background-color:#f5f7fa;}</style>""", unsafe_allow_html=True)

# ==========================================
# LOAD NSE STOCKS
# ==========================================
@st.cache_data(ttl=86400)
def load_nse500():
    try:
        url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
        headers = {"User-Agent":"Mozilla/5.0"}
        df = pd.read_csv(io.StringIO(requests.get(url, headers=headers, timeout=10).text))
        return sorted(df["Symbol"].unique())
    except:
        return ["RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","ITC"]

# ==========================================
# DATA DOWNLOAD
# ==========================================
@st.cache_data(ttl=300)
def get_data(symbol, interval, period):
    try:
        df = yf.download(f"{symbol}.NS", interval=interval, period=period, auto_adjust=True, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except:
        return pd.DataFrame()

# ==========================================
# INDICATORS
# ==========================================
def calculate_rsi(df, period=14):
    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calculate_atr(df, period=14):
    high_low = df["High"] - df["Low"]
    high_close = abs(df["High"] - df["Close"].shift(1))
    low_close = abs(df["Low"] - df["Close"].shift(1))
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(period).mean()

def calculate_adx(df, period=14):
    plus_dm = df["High"].diff()
    minus_dm = df["Low"].diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm > 0] = 0
    tr = calculate_atr(df, period)
    plus_di = 100 * (plus_dm.rolling(period).mean() / tr)
    minus_di = abs(100 * (minus_dm.rolling(period).mean() / tr))
    dx = (abs(plus_di - minus_di) / abs(plus_di + minus_di)) * 100
    return dx.rolling(period).mean()

def calculate_supertrend(df, period=10, multiplier=3):
    atr = calculate_atr(df, period)
    hl2 = (df["High"] + df["Low"]) / 2
    upper = hl2 + multiplier * atr
    lower = hl2 - multiplier * atr
    trend = [1]
    for i in range(1, len(df)):
        if df["Close"].iloc[i] > upper.iloc[i-1]:
            trend.append(1)
        elif df["Close"].iloc[i] < lower.iloc[i-1]:
            trend.append(-1)
        else:
            trend.append(trend[-1])
    df["ST_Direction"] = trend
    return df

def add_indicators(df):
    df["EMA20"] = df["Close"].ewm(span=20).mean()
    df["EMA50"] = df["Close"].ewm(span=50).mean()
    df["RSI"] = calculate_rsi(df)
    df["ATR"] = calculate_atr(df)
    df["ADX"] = calculate_adx(df)
    df["AVG_VOL"] = df["Volume"].rolling(20).mean()
    df["RVOL"] = df["Volume"] / df["AVG_VOL"]
    df["MACD"] = df["Close"].ewm(span=12).mean() - df["Close"].ewm(span=26).mean()
    df["MACD_SIGNAL"] = df["MACD"].ewm(span=9).mean()
    tp = (df["High"] + df["Low"] + df["Close"]) / 3
    df["VWAP"] = (tp * df["Volume"]).cumsum() / df["Volume"].cumsum()
    df = calculate_supertrend(df)
    return df

# ==========================================
# AI ENGINES + SCANNER LOGIC
# ==========================================
def predict_trend_ai(close_series):
    if len(close_series) < 30: return "NEUTRAL", 0
    y = close_series.tail(30).values; x = np.arange(len(y))
    slope, _ = np.polyfit(x, y, 1)
    corr =
