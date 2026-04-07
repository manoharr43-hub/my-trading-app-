import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="NSE Intraday Pro Scanner", layout="wide")
st_autorefresh(interval=10000, key="refresh")

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
    return yf.download(
        stocks,
        period="5d",
        interval="5m",
        group_by="ticker",
        progress=False
    )


# =============================
# INTRADAY ANALYSIS
# =============================
def analyze_intraday(df, ticker):
    try:
        if isinstance(df.columns, pd.MultiIndex):
            d = df[ticker].copy()
        else:
            d = df.copy()

        if d is None or len(d) < 30:
            return None

        # ✅ Only TODAY data
        d["Date"] = d.index.date
        today = d["Date"].iloc[-1]
        d = d[d["Date"] == today].copy()

        if len(d) < 20:
            return None

        close = d["Close"]
        high = d["High"]
        low = d["Low"]
        vol = d["Volume"]

        ltp = float(close.iloc[-1])

        # ✅ VWAP (Intraday)
        d["VWAP"] = (close * vol).cumsum() / vol.cumsum()

        # Indicators
        d["RSI"] = rsi(close)
        d["EMA20"] = ema(close, 20)
        d["EMA50"] = ema(close, 50)

        # ORB
        opening_high = high.iloc[:6].max()
        opening_low = low.iloc[:6].min()

        # Volume Spike
        avg_vol = vol.rolling(20).mean().iloc[-1]
        vol_spike = vol.iloc[-1] > avg_vol * 1.5

        # VWAP Trend
        vwap_trend_up = d["VWAP"].iloc[-1] > d["VWAP"].iloc[-5]
        vwap_trend_down = d["VWAP"].iloc[-1] < d["VWAP"].iloc[-5]

        # Default
        signal = "WAIT"
        color = "#ffffff"
        entry = 0
        target = 0
        sl = 0

        # BUY
        if (
            ltp > opening_high
            and ltp > d["VWAP"].iloc[-1]
            and d["RSI"].iloc[-1] > 55
            and vol_spike
            and vwap_trend_up
        ):
            signal = "INTRADAY BUY"
            color = "#d4edda"
            entry = round(ltp, 2)
            sl = round(d["VWAP"].iloc[-1], 2)
            target = round(entry + (entry - sl) * 2, 2)

        # SELL
        elif (
            ltp < opening_low
            and ltp < d["VWAP"].iloc[-1]
            and d["RSI"].iloc[-1] < 45
            and vol_spike
            and vwap_trend_down
        ):
            signal = "INTRADAY SELL"
            color = "#f8d7da"
            entry = round(ltp, 2)
            sl = round(d["VWAP"].iloc[-1], 2)
            target = round(entry - (sl - entry) * 2, 2)

        return {
            "Stock": ticker.replace(".NS", ""),
            "LTP": round(ltp, 2),
            "VWAP": round(d["VWAP"].iloc[-1], 2),
            "RSI": round(d["RSI"].iloc[-1], 1),
            "ORB High": round(opening_high, 2),
            "ORB Low": round(opening_low, 2),
            "Signal": signal,
            "Entry": entry,
            "Target": target,
            "SL": sl,
            "Volume Spike": "YES" if vol_spike else "NO",
            "Bg": color
        }

    except Exception as e:
        return None


# =============================
# UI
# =============================
st.title("🚀 NSE Intraday Pro Scanner")

sectors = {
    "Nifty 50": ["RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS", "TCS.NS", "INFY.NS"],
    "Auto": ["TATAMOTORS.NS", "MARUTI.NS", "M&M.NS"],
    "Bank": ["SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS"]
}

col1, col2 = st.columns(2)

with col1:
    sector = st.selectbox("Select Sector", list(sectors.keys()))

with col2:
    search = st.text_input("Search Stock").upper()


# =============================
# SEARCH
# =============================
if search:
    ticker = search + ".NS"
    data = yf.download(ticker, period="2d", interval="5m", progress=False)

    if not data.empty:
        res = analyze_intraday({ticker: data}, ticker)
        if res:
            st.subheader(f"🎯 {search} Analysis")
            st.write(res)


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

if results:
    df = pd.DataFrame(results)

    st.dataframe(
        df.style.apply(
            lambda x: [f"background-color: {df.loc[x.name, 'Bg']}"] * len(x),
            axis=1
        )
    )


# =============================
# ALERT
# =============================
strong = [r for r in results if r["Signal"] != "WAIT"]

if strong:
    st.warning("⚡ Intraday Trade Signals Found!")
