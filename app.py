import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="NSE Intraday AI Pro Scanner", layout="wide")
st_autorefresh(interval=20000, key="refresh")

# =============================
# ANALYSIS FUNCTION
# =============================
def analyze_stock(df):
    if df.empty or len(df) < 50:
        return df, 0, 0, 0, "Neutral"

    # RSI
    delta = df['Close'].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))

    # EMA
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    # VWAP
    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-9)

    # Volume
    avg_vol = df['Volume'].rolling(20).mean().iloc[-1]
    last_vol = df['Volume'].iloc[-1]
    vol_ratio = last_vol / (avg_vol + 1e-9)

    # Support & Resistance
    res = df['High'].iloc[-20:].max()
    sup = df['Low'].iloc[-20:].min()

    # AI Prediction
    X = np.array(range(10)).reshape(-1, 1)
    y = df['Close'].iloc[-10:].values
    model = LinearRegression().fit(X, y)
    prediction = model.predict([[10]])[0]

    current_price = df['Close'].iloc[-1]
    ai_view = "🚀 BULLISH" if prediction > current_price else "📉 BEARISH"

    return df, res, sup, vol_ratio, ai_view

# =============================
# NSE STOCKS
# =============================
stocks = ["RELIANCE.NS","TCS.NS","HDFCBANK.NS","ICICIBANK.NS","INFY.NS","SBIN.NS"]

# =============================
# SCANNER
# =============================
def run_scanner(tickers):
    data = yf.download(tickers, period="5d", interval="5m", group_by='ticker', progress=False)
    results = []

    for t in tickers:
        try:
            df = data[t].dropna()
            if df.empty:
                continue

            df, res, sup, vol_ratio, ai_view = analyze_stock(df)
            last = df.iloc[-1]

            ltp = round(last['Close'], 2)
            rsi = round(last['RSI'], 1)

            trend = "UPTREND" if last['EMA20'] > last['EMA50'] else "DOWNTREND"

            # STRONG SIGNAL LOGIC
            signal = "WAIT"
            entry = "-"
            sl = "-"
            target = "-"

            if (ltp > last['VWAP'] and trend == "UPTREND" and rsi > 50 and vol_ratio > 1.5 and ai_view == "🚀 BULLISH"):
                signal = "BUY"
                entry = ltp
                sl = round(sup, 2)
                target = round(ltp + (ltp - sl)*2, 2)

            elif (ltp < last['VWAP'] and trend == "DOWNTREND" and rsi < 50 and vol_ratio > 1.5 and ai_view == "📉 BEARISH"):
                signal = "SELL"
                entry = ltp
                sl = round(res, 2)
                target = round(ltp - (sl - ltp)*2, 2)

            results.append({
                "Stock": t.replace(".NS",""),
                "LTP": ltp,
                "RSI": rsi,
                "Trend": trend,
                "Volume": round(vol_ratio,2),
                "AI": ai_view,
                "Signal": signal,
                "Entry": entry,
                "Stoploss": sl,
                "Target": target
            })

        except:
            continue

    return pd.DataFrame(results)

# =============================
# UI
# =============================
st.title("🔥 NSE Intraday AI Smart Scanner")

df = run_scanner(stocks)

if not df.empty:
    st.dataframe(df, use_container_width=True)
    st.write(f"⏰ Last Update: {pd.Timestamp.now().strftime('%H:%M:%S')}")
