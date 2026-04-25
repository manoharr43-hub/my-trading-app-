import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V5", layout="wide")
st_autorefresh(interval=60000, key="refresh")

st.title("🚀 NSE AI PRO V5 - SMART MONEY + BACKTEST FOLDER")
st.markdown("---")

# =============================
# SESSION STATE
# =============================
if "bt_history" not in st.session_state:
    st.session_state.bt_history = []

# =============================
# DATA
# =============================
@st.cache_data(ttl=300)
def load_data(stock):
    return yf.Ticker(stock + ".NS").history(period="1d", interval="5m")

sector_map = {
    "Banking": ["HDFCBANK","ICICIBANK","SBIN","AXISBANK","KOTAKBANK"],
    "IT": ["TCS","INFY","HCLTECH","WIPRO","TECHM"],
    "Auto": ["MARUTI","M&M","TATAMOTORS"],
    "FMCG": ["ITC","RELIANCE","LT","BHARTIARTL"]
}

all_stocks = list(set(sum(sector_map.values(), [])))

# =============================
# RSI
# =============================
def rsi(df, period=14):
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# =============================
# AI PREDICT
# =============================
def ai_predict(df):
    df = df.copy().dropna()
    if len(df) < 30:
        return None

    df['Target'] = df['Close'].shift(-1)
    df.dropna(inplace=True)

    X = df[['Close','Volume']]
    y = df['Target']

    model = LinearRegression()
    model.fit(X, y)

    return model.predict(X.iloc[-1].values.reshape(1, -1))[0]

# =============================
# BIG PLAYER ENTRY
# =============================
def big_player(df):
    df = df.copy()

    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    df['AvgVol'] = df['Volume'].rolling(20).mean()

    last = df['Close'].iloc[-1]
    vol = df['Volume'].iloc[-1]
    avg_vol = df['AvgVol'].iloc[-1]

    resistance = df['High'].rolling(20).max().iloc[-2]
    support = df['Low'].rolling(20).min().iloc[-2]

    if last > resistance and vol > avg_vol * 1.5 and df['EMA20'].iloc[-1] > df['EMA50'].iloc[-1]:
        return "BUY", last

    elif last < support and vol > avg_vol * 1.5 and df['EMA20'].iloc[-1] < df['EMA50'].iloc[-1]:
        return "SELL", last

    return None, None

# =============================
# STRENGTH SCORE
# =============================
def strength(df):
    df = df.copy()

    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    df['AvgVol'] = df['Volume'].rolling(20).mean()

    score = 0

    if df['EMA20'].iloc[-1] > df['EMA50'].iloc[-1]:
        score += 2
    else:
        score -= 2

    if df['Volume'].iloc[-1] > df['AvgVol'].iloc[-1]:
        score += 1

    r = rsi(df).iloc[-1]
    if r < 70:
        score += 1
    else:
        score -= 1

    return score

# =============================
# ANALYSIS
# =============================
def analyze(df):
    if df is None or len(df) < 50:
        return None

    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    r = rsi(df)
    pred = ai_predict(df)

    signal = "WAIT"

    if pred:
        signal = "BUY" if pred > df['Close'].iloc[-1] else "SELL"

    vol_ok = df['Volume'].iloc[-1] > df['Volume'].rolling(20).mean().iloc[-1]

    trend_up = df['EMA20'].iloc[-1] > df['EMA50'].iloc[-1]
    trend_down = df['EMA20'].iloc[-1] < df['EMA50'].iloc[-1]

    final = "⚠️ WAIT"

    if signal == "BUY" and r.iloc[-1] < 70 and vol_ok and trend_up:
        final = "🚀 STRONG BUY"

    elif signal == "SELL" and r.iloc[-1] > 30 and vol_ok and trend_down:
        final = "💀 STRONG SELL"

    return signal, round(r.iloc[-1],2), final

# =============================
# BACKTEST RUN
# =============================
bt_date = st.sidebar.date_input("📅 Backtest Date", datetime.now().date() - timedelta(days=1))

if st.button("📊 RUN
