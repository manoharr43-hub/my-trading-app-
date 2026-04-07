import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="NSE Pro Scanner - Intraday", layout="wide")
# ప్రతి 10 సెకన్లకు ఆటోమేటిక్ రిఫ్రెష్
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
# DATA FETCH (1-Day for Pure Intraday)
# =============================
@st.cache_data(ttl=10)
def get_data(stocks):
    # ఇక్కడ period="1d" మార్చడం వల్ల కేవలం ఈరోజు డేటా మాత్రమే వస్తుంది
    return yf.download(stocks, period="1d", interval="5m", group_by="ticker", progress=False)

# =============================
# LOGIC
# =============================
def analyze(df, ticker):
    try:
        # మల్టీ-ఇండెక్స్ డేటాను హ్యాండిల్ చేయడం
        d = df[ticker].copy() if isinstance(df.columns, pd.MultiIndex) else df.copy()
        
        if len(d) < 20: # కనీసం కొన్ని క్యాండిల్స్ ఉండాలి
            return None

        close = d['Close']
        high = d['High']
        low = d['Low']
        vol = d['Volume']
        ltp = close.iloc[-1]

        # 1-Day Accurate VWAP
        d['VWAP'] = (close * vol).cumsum() / vol.cumsum()
        d['RSI'] = rsi(close)
        d['EMA20'] = ema(close, 20)
        
        # Pivot Points (నిన్నటి డేటా ఆధారంగా కాకుండా ఈరోజు రేంజ్ కోసం)
        # గమనిక: లైవ్ మార్కెట్ లో ఇది ఈరోజు హై/లో ని బట్టి మారుతుంది
        pivot = (high.max() + low.min() + close.iloc[-1]) / 3
        res = (2 * pivot) - low.min()
        sup = (2 * pivot) - high.max()

        # Volume Spike (గత 10 క్యాండిల్స్ సగటు కంటే 1.5 రెట్లు ఎక్కువ)
        avg_vol = vol.rolling(10).mean().iloc[-1]
        vol_spike = vol.iloc[-1] > avg_vol * 1.5

        signal = "WAIT"
        color = "#ffffff" # White

        # STRONG BUY Logic
        if ltp > d['VWAP'].iloc[-1] and d['RSI'].iloc[-1] > 55 and vol_spike:
            signal = "STRONG BUY"
            color = "#d4edda" # Light Green
        
        # STRONG SELL Logic
        elif ltp < d['VWAP'].iloc[-1] and d['RSI'].iloc[-1] < 45 and vol_spike:
            signal = "STRONG SELL"
            color = "#f8d7da" # Light Red

        return {
            "Stock": ticker.replace(".NS", ""),
            "LTP": round(ltp, 2),
            "VWAP": round(d['VWAP'].iloc[-1], 2),
            "RSI": round(d['RSI'].iloc[-1], 1),
            "Signal": signal,
            "Vol Spike": "YES" if vol_spike else "NO",
            "Color": color
        }
    except Exception as e:
        return None

# =============================
# MAIN APP UI
# =============================
st.title("📊 NSE Intraday Real-Time Scanner")

# మీకు కావలసిన స్టాక్స్ లిస్ట్ ఇక్కడ ఇచ్చుకోండి
watchlist = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "INFY.NS", "TATAMOTORS.NS"]

data = get_data(watchlist)
results = []

for ticker in watchlist:
    res = analyze(data, ticker)
    if res:
        results.append(res)

if results:
    df_display = pd.DataFrame(results)
    
    # సిగ్నల్ ని బట్టి రంగులు మార్చడం
    def highlight_signal(row):
        return [f'background-color: {row.Color}' for _ in row]

    st.table(df_display.drop(columns=['Color']).style.apply(highlight_signal, axis=1))
else:
    st.warning("డేటా లోడ్ అవ్వడం లేదు. దయచేసి మార్కెట్ సమయంలో ప్రయత్నించండి.")
