import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# =============================
# PAGE CONFIG
# =============================
st.set_page_config(page_title="🔥 Intraday AI Scanner V3", layout="wide")
st.title("🔥 Intraday AI Scanner V3 ULTRA (PRO FIXED)")

# =============================
# INPUT
# =============================
symbol = st.text_input("Enter Symbol (NSE use .NS)", "RELIANCE.NS")

# =============================
# DATA LOADER (SAFE)
# =============================
@st.cache_data(ttl=60)
def get_data(symbol):
    df = yf.download(symbol, period="5d", interval="5m", progress=False)
    return df

df = get_data(symbol)

if df is None or df.empty:
    st.error("❌ No data found. Check symbol.")
    st.stop()

# =============================
# CLEAN DATA
# =============================
df = df.dropna()

# =============================
# INDICATORS
# =============================
df["EMA9"] = df["Close"].ewm(span=9).mean()
df["EMA21"] = df["Close"].ewm(span=21).mean()
df["EMA50"] = df["Close"].ewm(span=50).mean()

delta = df["Close"].diff()
gain = delta.clip(lower=0).rolling(14).mean()
loss = (-delta.clip(upper=0)).rolling(14).mean()
rs = gain / loss
df["RSI"] = 100 - (100 / (1 + rs))

df["VOL_MA"] = df["Volume"].rolling(20).mean()

# =============================
# SAFE LAST ROW FUNCTION
# =============================
def val(x):
    if isinstance(x, (pd.Series, np.ndarray)):
        return float(x.iloc[-1])
    return float(x)

last = df.iloc[-1]

close = val(last["Close"])
ema9 = val(last["EMA9"])
ema21 = val(last["EMA21"])
ema50 = val(last["EMA50"])
rsi = val(last["RSI"])
vol = val(last["Volume"])
vol_ma = val(last["VOL_MA"])

# =============================
# TREND ENGINE
# =============================
bull = close > ema50 and ema9 > ema21
bear = close < ema50 and ema9 < ema21

vol_ok = vol > vol_ma

rsi_buy = 45 <= rsi <= 70
rsi_sell = 30 <= rsi <= 55

# =============================
# SMART CONFIDENCE SCORE
# =============================
score = 0
score += 30 if bull else 0
score += 25 if vol_ok else 0
score += 20 if rsi_buy or rsi_sell else 0
score += 15 if close > ema21 else 0
score += 10 if abs(ema9 - ema21) > 0 else 0

# =============================
# SIGNALS
# =============================
buy = bull and vol_ok and rsi_buy
sell = bear and vol_ok and rsi_sell

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
st.subheader("📊 AI Trading Signal")

if score < 40:
    st.warning("⏳ NO TRADE ZONE (LOW CONFIDENCE)")
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

st.line_chart(df[["Close", "EMA9", "EMA21", "EMA50"]])

# =============================
# DATA VIEW
# =============================
with st.expander("📊 Full Data"):
    st.dataframe(df.tail(100))
