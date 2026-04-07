import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="NSE Pro Scanner", layout="wide")

# రేట్ లిమిట్ ఎర్రర్ రాకుండా ఉండటానికి రిఫ్రెష్ టైమ్‌ను 30 సెకన్లకు పెంచాను
st_autorefresh(interval=30000, key="refresh")

# =============================
# INDICATORS
# =============================
def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# =============================
# DATA FETCH
# =============================
@st.cache_data(ttl=30) # TTL పెంచడం వల్ల సర్వర్ మీద లోడ్ తగ్గుతుంది
def get_data(stocks):
    try:
        return yf.download(stocks, period="1d", interval="5m", group_by="ticker", progress=False)
    except:
        return None

# =============================
# LOGIC
# =============================
def analyze(df, ticker):
    try:
        if isinstance(df.columns, pd.MultiIndex):
            d = df[ticker].copy()
        else:
            d = df.copy()
            
        if len(d) < 15: return None

        close = d['Close']
        vol = d['Volume']
        ltp = close.iloc[-1]

        d['VWAP'] = (close * vol).cumsum() / vol.cumsum()
        d['RSI'] = rsi(close)

        avg_vol = vol.rolling(10).mean().iloc[-1]
        vol_spike = vol.iloc[-1] > avg_vol * 1.5

        signal = "WAIT"
        bg_color = "#ffffff"

        if ltp > d['VWAP'].iloc[-1] and d['RSI'].iloc[-1] > 55 and vol_spike:
            signal = "STRONG BUY"
            bg_color = "#d4edda"
        elif ltp < d['VWAP'].iloc[-1] and d['RSI'].iloc[-1] < 45 and vol_spike:
            signal = "STRONG SELL"
            bg_color = "#f8d7da"

        return {
            "Stock": ticker.replace(".NS", ""),
            "LTP": round(ltp, 2),
            "VWAP": round(d['VWAP'].iloc[-1], 2),
            "RSI": round(d['RSI'].iloc[-1], 1),
            "Signal": signal,
            "Vol Spike": "YES" if vol_spike else "NO",
            "Color": bg_color
        }
    except:
        return None

# =============================
# MAIN APP UI
# =============================
st.title("📊 NSE Real-Time Intraday Scanner")

watchlist = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "INFY.NS", "TATAMOTORS.NS"]

data = get_data(watchlist)

if data is not None and not data.empty:
    results = []
    for ticker in watchlist:
        res = analyze(data, ticker)
        if res:
            results.append(res)

    if results:
        df_display = pd.DataFrame(results)
        def highlight_rows(row):
            return [f'background-color: {row.Color}' for _ in row]

        # వార్నింగ్ పోవడానికి ఇక్కడ width మార్చాను
        st.dataframe(
            df_display.drop(columns=['Color']).style.apply(highlight_rows, axis=1),
            width=None, # Auto width
            hide_index=True
        )
    else:
        st.info("విశ్లేషించడానికి తగినంత డేటా లేదు.")
else:
    st.error("Yahoo Finance నుండి డేటా రావడం లేదు. కాసేపు ఆగి మళ్ళీ ప్రయత్నించండి (Rate Limit).")
