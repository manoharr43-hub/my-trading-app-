import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# =============================
# PAGE CONFIG
# =============================
st.set_page_config(page_title="🔥 AI Trading Bot V5", layout="wide")
st.title("🔥 Intraday AI Trading Bot V5 (ULTIMATE)")

# =============================
# SYMBOL INPUT
# =============================
symbol = st.text_input("Enter Symbol (NSE use .NS)", "RELIANCE.NS")

# =============================
# DATA LOADER
# =============================
@st.cache_data(ttl=60)
def load(symbol):
    df = yf.download(symbol, period="5d", interval="5m", progress=False)

    # FIX MULTIINDEX
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    return df

df = load(symbol)

if df is None or df.empty:
    st.error("❌ No data found")
    st.stop()

df = df.dropna()

# =============================
# INDICATORS
# =============================
df["EMA9"] = df["Close"].ewm(span=9).mean()
df["EMA21"] = df["Close"].ewm(span=21).mean()
df["EMA50"] = df["Close"].ewm(span=50).mean()

# RSI
delta = df["Close"].diff()
gain = delta.clip(lower=0).rolling(14).mean()
loss = (-delta.clip(upper=0)).rolling(14).mean()
rs = gain / loss
df["RSI"] = 100 - (100 / (1 + rs))

# Volume
df["VOL_MA"] = df["Volume"].rolling(20).mean()

# VWAP (simple version)
df["VWAP"] = (df["Close"] * df["Volume"]).cumsum() / df["Volume"].cumsum()

# =============================
# LAST VALUE SAFE
# =============================
last = df.iloc[-1]

def safe(x):
    if isinstance(x, (pd.Series, np.ndarray)):
        return float(x.iloc[-1])
    return float(x)

close = safe(last["Close"])
ema9 = safe(last["EMA9"])
ema21 = safe(last["EMA21"])
ema50 = safe(last["EMA50"])
rsi = safe(last["RSI"])
vol = safe(last["Volume"])
vol_ma = safe(last["VOL_MA"])
vwap = safe(last["VWAP"])

# =============================
# TREND ENGINE
# =============================
bull = close > ema50 and ema9 > ema21 and close > vwap
bear = close < ema50 and ema9 < ema21 and close < vwap

volume_ok = vol > vol_ma

momentum_buy = 45 <= rsi <= 70
momentum_sell = 30 <= rsi <= 55

# =============================
# CONFIDENCE SCORE (0–100)
# =============================
score = 0
score += 25 if bull else 0
score += 20 if bear else 0
score += 20 if volume_ok else 0
score += 15 if momentum_buy or momentum_sell else 0
score += 10 if close > ema21 else 0
score += 10 if abs(ema9 - ema21) > 0 else 0

# =============================
# SIGNALS
# =============================
buy = bull and volume_ok and momentum_buy
sell = bear and volume_ok and momentum_sell

# =============================
# DASHBOARD
# =============================
col1, col2, col3, col4 = st.columns(4)

col1.metric("Price", round(close, 2))
col2.metric("RSI", round(rsi, 2))
col3.metric("Volume", int(vol))
col4.metric("Confidence", str(score) + "%")

# =============================
# SIGNAL PANEL
# =============================
st.subheader("📊 AI Signal Engine")

if score < 35:
    st.warning("⏳ NO TRADE ZONE")
elif buy:
    st.success("🔥 STRONG BUY SIGNAL")
elif sell:
    st.error("🔴 STRONG SELL SIGNAL")
else:
    st.info("⚡ WAIT FOR CONFIRMATION")

# =============================
# CHART
# =============================
st.subheader("📈 Market Trend")

st.line_chart(df[["Close", "EMA9", "EMA21", "EMA50", "VWAP"]])

# =============================
# DATA TABLE
# =============================
with st.expander("📊 Full Data"):
    st.dataframe(df.tail(100))
