import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="NSE Pro Scanner", layout="wide")

# ప్రతి 10 సెకన్లకు పేజీ ఆటోమేటిక్ గా రిఫ్రెష్ అవుతుంది
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
# DATA FETCH (1-Day for Accurate VWAP)
# =============================
@st.cache_data(ttl=10)
def get_data(stocks):
    # period="1d" వల్ల కేవలం ఈరోజు డేటా మాత్రమే వస్తుంది (Intraday కోసం ఉత్తమం)
    return yf.download(stocks, period="1d", interval="5m", group_by="ticker", progress=False)

# =============================
# LOGIC
# =============================
def analyze(df, ticker):
    try:
        # మల్టీ-ఇండెక్స్ డేటాను సరిగ్గా తీసుకోవడం
        if isinstance(df.columns, pd.MultiIndex):
            d = df[ticker].copy()
        else:
            d = df.copy()
            
        if len(d) < 15: # కనీసం కొన్ని డేటా పాయింట్స్ ఉండాలి
            return None

        close = d['Close']
        high = d['High']
        low = d['Low']
        vol = d['Volume']
        ltp = close.iloc[-1]

        # 1-Day Accurate VWAP Calculation
        d['VWAP'] = (close * vol).cumsum() / vol.cumsum()
        d['RSI'] = rsi(close)
        d['EMA20'] = ema(close, 20)

        # Volume Spike Logic (గత 10 క్యాండిల్స్ సగటు కంటే 1.5 రెట్లు ఎక్కువ)
        avg_vol = vol.rolling(10).mean().iloc[-1]
        vol_spike = vol.iloc[-1] > avg_vol * 1.5

        signal = "WAIT"
        bg_color = "#ffffff" # Default White

        # BUY & SELL LOGIC
        if ltp > d['VWAP'].iloc[-1] and d['RSI'].iloc[-1] > 55 and vol_spike:
            signal = "STRONG BUY"
            bg_color = "#d4edda" # Light Green
        elif ltp < d['VWAP'].iloc[-1] and d['RSI'].iloc[-1] < 45 and vol_spike:
            signal = "STRONG SELL"
            bg_color = "#f8d7da" # Light Red

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

# మీ వాచ్‌లిస్ట్
watchlist = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "INFY.NS", "TATAMOTORS.NS", "ITC.NS"]

# డేటా లోడ్ చేయడం
data = get_data(watchlist)
results = []

for ticker in watchlist:
    res = analyze(data, ticker)
    if res:
        results.append(res)

if results:
    df_display = pd.DataFrame(results)
    
    # సిగ్నల్ ని బట్టి రంగులు మార్చే ఫంక్షన్
    def highlight_rows(row):
        return [f'background-color: {row.Color}' for _ in row]

    # పాత st.table బదులుగా కొత్త st.dataframe వాడుతున్నాం (ఎర్రర్ రాకుండా ఉండటానికి)
    st.dataframe(
        df_display.drop(columns=['Color']).style.apply(highlight_rows, axis=1),
        use_container_width=True,
        hide_index=True
    )
    
    st.caption("గమనిక: ఈ డేటా ప్రతి 10 సెకన్లకు ఒకసారి ఆటోమేటిక్ గా అప్‌డేట్ అవుతుంది.")
else:
    st.error("డేటా అందుబాటులో లేదు. దయచేసి మార్కెట్ సమయంలో (9:15 AM - 3:30 PM) చెక్ చేయండి.")
