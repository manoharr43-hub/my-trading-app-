import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# =============================
# PAGE CONFIG
# =============================
st.set_page_config(page_title="🔥 AI Intraday Scanner V2", layout="wide")

st.title("🔥 Intraday AI Trading Scanner V2 (PRO)")

# =============================
# INPUT
# =============================
symbol = st.text_input("Enter Symbol (NSE use .NS)", "RELIANCE.NS")

# =============================
# LOAD DATA (SAFE)
# =============================
@st.cache_data(ttl=60)
def load_data(symbol):
    df = yf.download(symbol, period="5d", interval="5m", progress=False)
    return df

data = load_data(symbol)

if data is None or data.empty:
    st.error("❌ No data found. Try correct symbol like RELIANCE.NS")
    st.stop()

# =============================
# INDICATORS
# =============================
data["EMA9"] = data["Close"].ewm(span=9).mean()
data["EMA21"] = data["Close"].ewm(span=21).mean()
data["EMA50"] = data["Close"].ewm(span=50).mean()

# RSI
delta = data["Close"].diff()
gain = delta.clip(lower=0).rolling(14).mean()
loss = (-delta.clip(upper=0)).rolling(14).mean()
rs = gain / loss
data["RSI"] = 100 - (100 / (1 + rs))

# Volume MA
data["VOL_MA"] = data["Volume"].rolling(20).mean()

# =============================
# LAST VALID ROW (SAFE CLEAN)
# =============================
last = data.dropna().iloc[-1]

close = float(last["Close"])
ema9 = float(last["EMA9"])
ema21 = float(last["EMA21"])
ema50 = float(last["EMA50"])
rsi = float(last["RSI"])
vol = float(last["Volume"])
vol_ma = float(last["VOL_MA"])

# =============================
# TREND LOGIC
# =============================
bull_trend = close > ema50 and ema9 > ema21
bear_trend = close < ema50 and ema9 < ema21

volume_ok = vol > vol_ma

rsi_buy_zone = 45 <= rsi <= 70
rsi_sell_zone = 30 <= rsi <= 55

# =============================
# CONFIDENCE SCORE (0–100)
# =============================
score = 0
score += 25 if bull_trend else 0
score += 25 if volume_ok else 0
score += 20 if rsi_buy_zone or rsi_sell_zone else 0
score += 15 if abs(ema9 - ema21) > 0 else 0
score += 15 if close > ema21 else 0

confidence = score

# =============================
# SIGNAL ENGINE
# =============================
buy_signal = bull_trend and volume_ok and rsi_buy_zone
sell_signal = bear_trend and volume_ok and rsi_sell_zone

# =============================
# DASHBOARD
# =============================
col1, col2, col3, col4 = st.columns(4)

col1.metric("Price", round(close, 2))
col2.metric("RSI", round(rsi, 2))
col3.metric("Volume", int(vol))
col4.metric("Confidence", str(confidence) + "%")

# =============================
# SIGNAL DISPLAY
# =============================
st.subheader("📊 AI Signal")

if confidence < 40:
    st.warning("⏳ NO TRADE ZONE (LOW CONFIDENCE)")
elif buy_signal:
    st.success("🔥 STRONG BUY SIGNAL")
elif sell_signal:
    st.error("🔴 STRONG SELL SIGNAL")
else:
    st.info("⚡ WAIT FOR CONFIRMATION")

# =============================
# CHART
# =============================
st.subheader("📈 Trend Chart")
st.line_chart(data[["Close", "EMA9", "EMA21", "EMA50"]])

# =============================
# RAW DATA
# =============================
with st.expander("📊 Show Data"):
    st.dataframe(data.tail(50))
