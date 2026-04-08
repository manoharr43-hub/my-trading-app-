import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="NSE PRO FIXED", layout="wide")
st_autorefresh(interval=20000, key="refresh")

# =============================
# SAFE STOCK LIST (NO ERROR)
# =============================
stocks = [
    "RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS",
    "SBIN.NS","LT.NS","ITC.NS","WIPRO.NS","AXISBANK.NS"
]

# =============================
# ANALYSIS
# =============================
def analyze_stock(df):
    if df.empty or len(df) < 50:
        return None

    df = df.copy()

    delta = df['Close'].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))

    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-9)

    avg_vol = df['Volume'].rolling(20).mean().iloc[-1]
    last_vol = df['Volume'].iloc[-1]
    vol_ratio = last_vol / (avg_vol + 1e-9)

    res = df['High'].iloc[-20:].max()
    sup = df['Low'].iloc[-20:].min()

    # AI
    X = np.arange(10).reshape(-1, 1)
    y = df['Close'].iloc[-10:].values
    model = LinearRegression().fit(X, y)
    prediction = model.predict([[10]])[0]

    current_price = df['Close'].iloc[-1]
    ai_view = "🚀 BULLISH" if prediction > current_price else "📉 BEARISH"

    return df, res, sup, vol_ratio, ai_view

# =============================
# BREAKOUT
# =============================
def check_breakout(df):
    recent_high = df['High'].iloc[-20:-1].max()
    recent_low = df['Low'].iloc[-20:-1].min()
    last_close = df['Close'].iloc[-1]

    if last_close > recent_high:
        return "🚀 BREAKOUT"
    elif last_close < recent_low:
        return "📉 BREAKDOWN"
    else:
        return "NONE"

# =============================
# SCANNER
# =============================
def run_scanner(tickers):
    results = []

    for t in tickers:
        try:
            df = yf.download(t, period="5d", interval="5m", progress=False)
            df = df.dropna()

            result = analyze_stock(df)
            if result is None:
                continue

            df, res, sup, vol_ratio, ai_view = result
            breakout = check_breakout(df)

            last = df.iloc[-1]

            ltp = round(last['Close'], 2)
            rsi = round(last['RSI'], 1)
            trend = "UPTREND" if last['EMA20'] > last['EMA50'] else "DOWNTREND"

            signal = "WAIT"

            if (ltp > last['VWAP'] and trend == "UPTREND" and ai_view == "🚀 BULLISH"):
                signal = "BUY"

            elif (ltp < last['VWAP'] and trend == "DOWNTREND" and ai_view == "📉 BEARISH"):
                signal = "SELL"

            if breakout == "🚀 BREAKOUT" and vol_ratio > 1.5:
                signal = "STRONG BUY"
            elif breakout == "📉 BREAKDOWN" and vol_ratio > 1.5:
                signal = "STRONG SELL"

            results.append({
                "Stock": t.replace(".NS",""),
                "LTP": ltp,
                "RSI": rsi,
                "Trend": trend,
                "Volume": round(vol_ratio,2),
                "AI": ai_view,
                "Breakout": breakout,
                "Signal": signal
            })

        except Exception as e:
            st.warning(f"{t} error: {e}")

    return pd.DataFrame(results)

# =============================
# UI
# =============================
st.title("🔥 NSE PRO STABLE SCANNER")

df = run_scanner(stocks)

if not df.empty:
    st.dataframe(df, use_container_width=True)

    # LIVE CHART (WORKING)
    selected = st.selectbox("Select Stock", df['Stock'])

    if selected:
        st.markdown(f"""
        <iframe src="https://www.tradingview.com/chart/?symbol=NSE:{selected}"
        width="100%" height="500"></iframe>
        """, unsafe_allow_html=True)

else:
    st.warning("No signals found")
