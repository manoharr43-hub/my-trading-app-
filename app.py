import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="NSE Intraday Pro Scanner", layout="wide")
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
@st.cache_data(ttl=20)
def get_data(stocks):
    return yf.download(stocks, period="5d", interval="5m", group_by="ticker", progress=False)

# =============================
# ANALYSIS
# =============================
def analyze_intraday(df, ticker):
    try:
        d = df[ticker].copy() if isinstance(df.columns, pd.MultiIndex) else df.copy()

        if d is None or len(d) < 50:
            return None

        # Only today data
        d["Date"] = d.index.date
        today = d["Date"].iloc[-1]
        d = d[d["Date"] == today].copy()

        if len(d) < 30:
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

        # Volume
        avg_vol = vol.rolling(20).mean().iloc[-1]
        vol_spike = vol.iloc[-1] > avg_vol * 1.5

        # Signal
        signal = "WAIT"
        color = "#ffffff"

        if ltp > resistance and ltp > d["VWAP"].iloc[-1] and trend == "UPTREND" and vol_spike:
            signal = "BUY"
            color = "#d4edda"

        elif ltp < support and ltp < d["VWAP"].iloc[-1] and trend == "DOWNTREND" and vol_spike:
            signal = "SELL"
            color = "#f8d7da"

        return {
            "Stock": ticker.replace(".NS", ""),
            "LTP": round(ltp, 2),
            "Support": support,
            "Resistance": resistance,
            "ORB High": orb_high,
            "ORB Low": orb_low,
            "RSI": round(d["RSI"].iloc[-1], 1),
            "Trend": trend,
            "Signal": signal,
            "Volume": "YES" if vol_spike else "NO",
            "Bg": color
        }

    except:
        return None

# =============================
# UI
# =============================
st.title("🚀 NSE Intraday Pro Scanner")

sectors = {
    "Nifty 50": ["RELIANCE.NS","TCS.NS","HDFCBANK.NS","ICICIBANK.NS","INFY.NS"],
    "Bank": ["SBIN.NS","AXISBANK.NS","KOTAKBANK.NS"],
    "IT": ["TCS.NS","INFY.NS","WIPRO.NS"],
    "Auto": ["TATAMOTORS.NS","MARUTI.NS","M&M.NS"]
}

sector = st.selectbox("Select Sector", list(sectors.keys()))

# =============================
# SCANNER
# =============================
data = get_data(sectors[sector])
results = []

if data is not None:
    for s in sectors[sector]:
        r = analyze_intraday(data, s)
        if r:
            results.append(r)

# =============================
# DISPLAY (FIXED NO ERROR)
# =============================
if results:
    df = pd.DataFrame(results)

    def highlight(row):
        return [f'background-color: {row["Bg"]}'] * len(row)

    st.dataframe(
        df.drop(columns=["Bg"]).style
        .format({"LTP": "{:.2f}", "RSI": "{:.1f}"})
        .apply(highlight, axis=1)
    )

# =============================
# ALERT
# =============================
strong = [r for r in results if r["Signal"] != "WAIT"]

if strong:
    st.warning("⚡ Intraday Signals Found!")
