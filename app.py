import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="NSE Pro Scanner", layout="wide")
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
    return yf.download(stocks, period="5d", interval="5m", group_by="ticker", progress=False)

# =============================
# ANALYSIS FUNCTION
# =============================
def analyze_intraday(df, ticker):
    try:
        d = df[ticker].copy() if isinstance(df.columns, pd.MultiIndex) else df.copy()

        if d is None or len(d) < 30:
            return None

        # 👉 Only today data
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

        # =============================
        # VWAP
        # =============================
        d["VWAP"] = (close * vol).cumsum() / vol.cumsum()

        # =============================
        # RSI + EMA
        # =============================
        d["RSI"] = rsi(close)
        d["EMA20"] = ema(close, 20)
        d["EMA50"] = ema(close, 50)

        # =============================
        # ORB
        # =============================
        orb_high = high.iloc[:6].max()
        orb_low = low.iloc[:6].min()

        # =============================
        # SUPPORT & RESISTANCE
        # =============================
        pivot = (high.iloc[-2] + low.iloc[-2] + close.iloc[-2]) / 3
        resistance = (2 * pivot) - low.iloc[-2]
        support = (2 * pivot) - high.iloc[-2]

        # =============================
        # VOLUME
        # =============================
        avg_vol = vol.rolling(20).mean().iloc[-1]
        vol_spike = vol.iloc[-1] > avg_vol * 1.5

        # =============================
        # SIGNAL + COLOR
        # =============================
        signal = "WAIT"
        color = "#ffffff"
        entry = target = sl = 0

        # 🔵 BREAKOUT
        if ltp > resistance:
            signal = "BREAKOUT"
            color = "#cce5ff"
            entry = ltp
            sl = support
            target = entry + (entry - sl) * 2

        # 🔴 BREAKDOWN
        elif ltp < support:
            signal = "BREAKDOWN"
            color = "#f8d7da"
            entry = ltp
            sl = resistance
            target = entry - (sl - entry) * 2

        return {
            "Stock": ticker.replace(".NS", ""),
            "LTP": round(ltp, 2),
            "Support": round(support, 2),
            "Resistance": round(resistance, 2),
            "VWAP": round(d["VWAP"].iloc[-1], 2),
            "RSI": round(d["RSI"].iloc[-1], 1),
            "ORB High": round(orb_high, 2),
            "ORB Low": round(orb_low, 2),
            "Signal": signal,
            "Entry": round(entry, 2),
            "Target": round(target, 2),
            "SL": round(sl, 2),
            "Volume": "YES" if vol_spike else "NO",
            "Bg": color
        }

    except:
        return None

# =============================
# UI
# =============================
st.title("🚀 NSE Intraday Pro Scanner")

# ✅ NIFTY 500 (Top Liquid Stocks)
sectors = {
    "Nifty 50": ["RELIANCE.NS","HDFCBANK.NS","ICICIBANK.NS","TCS.NS","INFY.NS"],
    "Auto": ["TATAMOTORS.NS","MARUTI.NS","M&M.NS"],
    "Bank": ["SBIN.NS","AXISBANK.NS","KOTAKBANK.NS"],
    "IT": ["TCS.NS","INFY.NS","WIPRO.NS","HCLTECH.NS"],
    "Pharma": ["SUNPHARMA.NS","CIPLA.NS","DRREDDY.NS"],
    "Metal": ["TATASTEEL.NS","JSWSTEEL.NS","HINDALCO.NS"],

    "Nifty 500": [
        "RELIANCE.NS","TCS.NS","HDFCBANK.NS","ICICIBANK.NS","INFY.NS",
        "ITC.NS","SBIN.NS","LT.NS","BHARTIARTL.NS","KOTAKBANK.NS",
        "AXISBANK.NS","ASIANPAINT.NS","MARUTI.NS","HCLTECH.NS",
        "WIPRO.NS","TATASTEEL.NS","JSWSTEEL.NS","HINDALCO.NS",
        "SUNPHARMA.NS","DRREDDY.NS","CIPLA.NS","ULTRACEMCO.NS",
        "POWERGRID.NS","NTPC.NS","ONGC.NS","ADANIPORTS.NS",
        "ADANIENT.NS","BAJFINANCE.NS","BAJAJFINSV.NS","HEROMOTOCO.NS"
    ]
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

if results:
    df = pd.DataFrame(results)

    st.dataframe(
        df.style.format({
            "LTP": "{:.2f}",
            "Support": "{:.2f}",
            "Resistance": "{:.2f}",
            "VWAP": "{:.2f}",
            "Entry": "{:.2f}",
            "Target": "{:.2f}",
            "SL": "{:.2f}"
        }).apply(
            lambda x: [f"background-color: {df.loc[x.name, 'Bg']}"] * len(x),
            axis=1
        )
    )

# =============================
# ALERT
# =============================
strong = [r for r in results if r["Signal"] != "WAIT"]

if strong:
    st.warning("⚡ Breakout / Breakdown Signals Found!")
