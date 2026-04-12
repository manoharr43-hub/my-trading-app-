import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# =============================
# PAGE CONFIG
# =============================
st.set_page_config(page_title="🔥 Intraday AI Scanner", layout="wide")

st.title("🔥 Intraday AI Trading Scanner (V1)")

# =============================
# INPUT
# =============================
symbol = st.text_input("Enter Symbol (NSE use .NS)", "RELIANCE.NS")

# =============================
# DATA LOADING
# =============================
data = yf.download(symbol, period="5d", interval="5m")

if data.empty:
    st.error("No data found. Check symbol.")
    st.stop()

# =============================
# INDICATORS
# =============================
data["EMA9"] = data["Close"].ewm(span=9).mean()
data["EMA21"] = data["Close"].ewm(span=21).mean()
data["EMA50"] = data["Close"].ewm(span=50).mean()

delta = data["Close"].diff()
gain = (delta.where(delta > 0, 0)).rolling(14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
rs = gain / loss
data["RSI"] = 100 - (100 / (1 + rs))

data["VOL_MA"] = data["Volume"].rolling(20).mean()

# =============================
# LAST ROW VALUES
# =============================
last = data.iloc[-1]

close = last["Close"]
ema9 = last["EMA9"]
ema21 = last["EMA21"]
ema50 = last["EMA50"]
rsi = last["RSI"]
vol = last["Volume"]
vol_ma = last["VOL_MA"]

# =============================
# SIGNAL LOGIC
# =============================
trend_bull = close > ema50 and ema9 > ema21
trend_bear = close < ema50 and ema9 < ema21

volume_strong = vol > vol_ma
rsi_ok_buy = rsi < 70 and rsi > 40
rsi_ok_sell = rsi > 30 and rsi < 60

buy_signal = trend_bull and volume_strong and rsi_ok_buy
sell_signal = trend_bear and volume_strong and rsi_ok_sell

# =============================
# DASHBOARD
# =============================
col1, col2, col3, col4 = st.columns(4)

col1.metric("Price", round(close, 2))
col2.metric("RSI", round(rsi, 2))
col3.metric("Volume", int(vol))
col4.metric("Vol Avg", int(vol_ma) if not np.isnan(vol_ma) else 0)

# =============================
# SIGNAL DISPLAY
# =============================
st.subheader("📊 Signal Status")

if buy_signal:
    st.success("🔥 STRONG BUY SIGNAL")
elif sell_signal:
    st.error("🔴 STRONG SELL SIGNAL")
else:
    st.warning("⏳ WAIT / NO CLEAR SIGNAL")

# =============================
# CHART
# =============================
st.line_chart(data[["Close", "EMA9", "EMA21", "EMA50"]])

# =============================
# TABLE
# =============================
st.subheader("📌 Latest Data")
st.dataframe(data.tail(20))
