import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# =============================
# PAGE CONFIG
# =============================
st.set_page_config(page_title="🔥 Intraday AI Scanner V4", layout="wide")
st.title("🔥 Intraday AI Scanner V4 ULTRA (NEW BUILD)")

# =============================
# INPUT
# =============================
symbol = st.text_input("Enter Symbol (NSE use .NS)", "RELIANCE.NS")

# =============================
# DATA LOADER
# =============================
@st.cache_data(ttl=60)
def fetch_data(symbol):
    df = yf.download(symbol, period="5d", interval="5m", progress=False)

    # FIX: flatten multiindex if exists
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    return df

df = fetch_data(symbol)

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

# RSI
delta = df["Close"].diff()
gain = delta.clip(lower=0).rolling(14).mean()
loss = (-delta.clip(upper=0)).rolling(14).mean()
rs = gain / loss
df["RSI"] = 100 - (100 / (1 + rs))

# Volume
df["VOL_MA"] = df["Volume"].rolling(20).mean()

# =============================
# SAFE LAST ROW
# =============================
last = df.iloc[-1]

def v(x):
    if isinstance(x, (pd.Series, np.ndarray)):
        return float(x.iloc[-1])
    return float(x)

close = v(last["Close"])
ema9 = v(last["EMA9"])
ema21 = v(last["EMA21"])
ema50 = v(last["EMA50"])
rsi = v(last["RSI"])
vol = v(last["Volume"])
vol_ma = v(last["VOL_MA"])

# =============================
# TREND ENGINE
# =============================
bull_trend = close > ema50 and ema9 > ema21
bear_trend = close < ema50 and ema9 < ema21

volume_ok = vol > vol_ma

rsi_buy_zone = 45 <= rsi <= 70
rsi_sell_zone = 30 <= rsi <= 55

# =============================
# CONFIDENCE SCORE
# =============================
score = 0
score += 30 if bull_trend else 0
score += 25 if volume_ok else 0
score += 20 if rsi_buy_zone or rsi_sell_zone else 0
score += 15 if close > ema21 else 0
score += 10 if abs(ema9 - ema21) > 0 else 0

# =============================
# SIGNALS
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
col4.metric("Confidence", str(score) + "%")

# =============================
# SIGNAL PANEL
# =============================
st.subheader("📊 AI Signal Engine")

if score < 40:
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
st.subheader("📈 Market Trend")

chart = df[["Close", "EMA9", "EMA21", "EMA50"]]

st.line_chart(chart)

# =============================
# DATA VIEW
# =============================
with st.expander("📊 FULL DATA"):
    st.dataframe(df.tail(100))
