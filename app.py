import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="NSE Smart Scanner", layout="wide")
st_autorefresh(interval=15000, key="refresh")

# =============================
# INDICATORS
# =============================
def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    rs = gain / loss
    rsi_val = 100 - (100 / (1 + rs))
    return rsi_val.fillna(0)   # ✅ FIX

def ema(series, span):
    return series.ewm(span=span, adjust=False).mean()

# =============================
# DATA
# =============================
@st.cache_data(ttl=30)
def get_data(stocks):
    try:
        return yf.download(stocks, period="5d", interval="5m", group_by="ticker", progress=False)
    except:
        return None

# =============================
# ANALYSIS
# =============================
def analyze(df, ticker):
    try:
        d = df[ticker].copy() if isinstance(df.columns, pd.MultiIndex) else df.copy()

        if d is None or len(d) < 20:
            return None

        d["Date"] = d.index.date
        today = d["Date"].iloc[-1]
        d = d[d["Date"] == today].copy()

        if len(d) < 10:
            return None

        close = d["Close"]
        high = d["High"]
        low = d["Low"]
        vol = d["Volume"]

        ltp = float(close.iloc[-1])

        # VWAP
        d["VWAP"] = (close * vol).cumsum() / vol.cumsum()

        # RSI FIX
        d["RSI"] = rsi(close)
        rsi_val = round(float(d["RSI"].iloc[-1]), 1)

        # ORB
        orb_high = round(high.iloc[:6].max(), 2)
        orb_low = round(low.iloc[:6].min(), 2)

        # Trend
        d["EMA20"] = ema(close, 20)
        d["EMA50"] = ema(close, 50)

        trend = "SIDEWAYS"
        if d["EMA20"].iloc[-1] > d["EMA50"].iloc[-1]:
            trend = "UPTREND"
        elif d["EMA20"].iloc[-1] < d["EMA50"].iloc[-1]:
            trend = "DOWNTREND"

        # Signal
        signal = "BUY" if ltp > d["VWAP"].iloc[-1] else "SELL"

        return {
            "Stock": ticker.replace(".NS",""),
            "LTP": round(ltp,2),
            "RSI": rsi_val,
            "ORB High": orb_high,
            "ORB Low": orb_low,
            "Trend": trend,
            "Signal": signal
        }

    except:
        return None

# =============================
# UI
# =============================
st.title("🚀 NSE Smart Scanner (RSI FIXED)")

# ✅ NSE SECTORS FULL
sectors = {
    "Nifty 50": ["RELIANCE.NS","TCS.NS","HDFCBANK.NS","ICICIBANK.NS","INFY.NS"],
    "Banking": ["SBIN.NS","HDFCBANK.NS","ICICIBANK.NS","AXISBANK.NS","KOTAKBANK.NS"],
    "IT": ["TCS.NS","INFY.NS","WIPRO.NS","HCLTECH.NS","TECHM.NS"],
    "Auto": ["TATAMOTORS.NS","MARUTI.NS","M&M.NS","BAJAJ-AUTO.NS"],
    "Pharma": ["SUNPHARMA.NS","DRREDDY.NS","CIPLA.NS","DIVISLAB.NS"],
    "Metal": ["TATASTEEL.NS","JSWSTEEL.NS","HINDALCO.NS"],
    "FMCG": ["ITC.NS","HINDUNILVR.NS","DABUR.NS","BRITANNIA.NS"],
    "Energy": ["RELIANCE.NS","ONGC.NS","NTPC.NS","POWERGRID.NS"]
}

col1, col2 = st.columns(2)

with col1:
    sector = st.selectbox("Select NSE Sector", list(sectors.keys()))

with col2:
    trend_filter = st.selectbox("Trend", ["ALL","UPTREND","DOWNTREND","SIDEWAYS"])

# =============================
# LOAD
# =============================
limit = st.slider("Stocks",5,15,10)
stocks = sectors[sector][:limit]

with st.spinner("Loading data..."):
    data = get_data(stocks)

# =============================
# SCAN
# =============================
results = []

if data is not None:
    for s in stocks:
        r = analyze(data, s)
        if r:
            results.append(r)

# =============================
# FILTER
# =============================
if trend_filter != "ALL":
    temp = [r for r in results if r["Trend"] == trend_filter]
    if temp:
        results = temp

# =============================
# DISPLAY
# =============================
if results:
    df = pd.DataFrame(results)
    st.dataframe(df)
else:
    st.warning("No stocks found")

# =============================
# ALERT
# =============================
if any(r["Signal"]=="BUY" for r in results):
    st.success("🔥 BUY Signals Available")
