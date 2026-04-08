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
    return 100 - (100 / (1 + rs))

def ema(series, span):
    return series.ewm(span=span, adjust=False).mean()

# =============================
# DATA FETCH
# =============================
@st.cache_data(ttl=30)
def get_data(stocks):
    try:
        data = yf.download(stocks, period="5d", interval="5m", group_by="ticker", progress=False)
        return data
    except:
        return None

# =============================
# ANALYSIS
# =============================
def analyze_intraday(df, ticker):
    try:
        # Handle multi ticker data
        if isinstance(df.columns, pd.MultiIndex):
            d = df[ticker].copy()
        else:
            d = df.copy()

        if d is None or len(d) < 20:
            return None

        # Only today's data
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

        # RSI
        d["RSI"] = rsi(close)

        # ORB
        orb_high = round(high.iloc[:6].max(), 2)
        orb_low = round(low.iloc[:6].min(), 2)

        # Support / Resistance
        pivot = (high.iloc[-2] + low.iloc[-2] + close.iloc[-2]) / 3
        resistance = round((2 * pivot) - low.iloc[-2], 2)
        support = round((2 * pivot) - high.iloc[-2], 2)

        # Trend
        d["EMA20"] = ema(close, 20)
        d["EMA50"] = ema(close, 50)

        trend = "SIDEWAYS"
        if d["EMA20"].iloc[-1] > d["EMA50"].iloc[-1]:
            trend = "UPTREND"
        elif d["EMA20"].iloc[-1] < d["EMA50"].iloc[-1]:
            trend = "DOWNTREND"

        # Signal
        signal = "WAIT"
        if ltp > d["VWAP"].iloc[-1]:
            signal = "BUY"
        elif ltp < d["VWAP"].iloc[-1]:
            signal = "SELL"

        return {
            "Stock": ticker.replace(".NS", ""),
            "LTP": round(ltp, 2),
            "Support": support,
            "Resistance": resistance,
            "ORB High": orb_high,
            "ORB Low": orb_low,
            "RSI": round(d["RSI"].iloc[-1], 1),
            "Trend": trend,
            "Signal": signal
        }

    except Exception as e:
        return None

# =============================
# UI
# =============================
st.title("🚀 NSE Smart Scanner (Error-Free)")

sectors = {
    "Nifty 50": ["RELIANCE.NS","TCS.NS","HDFCBANK.NS","ICICIBANK.NS","INFY.NS"],
    "Bank": ["SBIN.NS","AXISBANK.NS","KOTAKBANK.NS"],
    "IT": ["TCS.NS","INFY.NS","WIPRO.NS"],
    "Auto": ["TATAMOTORS.NS","MARUTI.NS","M&M.NS"]
}

col1, col2 = st.columns(2)

with col1:
    sector = st.selectbox("Select Sector", list(sectors.keys()))

with col2:
    trend_filter = st.selectbox("Select Trend", ["ALL", "UPTREND", "DOWNTREND", "SIDEWAYS"])

# =============================
# LOAD DATA
# =============================
limit = st.slider("Stocks Count", 5, 15, 10)
stocks = sectors[sector][:limit]

with st.spinner("Fetching data... ⏳"):
    data = get_data(stocks)

# =============================
# SCAN
# =============================
results = []

if data is not None:
    for s in stocks:
        res = analyze_intraday(data, s)
        if res:
            results.append(res)

# =============================
# FILTER (SAFE)
# =============================
all_results = results.copy()

if trend_filter != "ALL":
    filtered = [r for r in results if r["Trend"] == trend_filter]
    if len(filtered) > 0:
        results = filtered
    else:
        st.warning("⚠️ No stocks in selected trend → Showing ALL")
        results = all_results

# =============================
# DISPLAY
# =============================
if results:
    df = pd.DataFrame(results)
    st.dataframe(df)
else:
    st.error("No data available")

# =============================
# ALERT
# =============================
signals = [r for r in results if r["Signal"] != "WAIT"]

if signals:
    st.success("🔥 Signals Available!")
