import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="NSE Scanner FIXED", layout="wide")
st_autorefresh(interval=20000, key="refresh")

# =============================
# ANALYSIS
# =============================
def analyze_stock(df):
    try:
        if df.empty or len(df) < 50:
            return None

        df = df.copy()

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

        # Support / Resistance
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

    except Exception as e:
        return None

# =============================
# STOCK LIST
# =============================
stocks = ["RELIANCE.NS","TCS.NS","HDFCBANK.NS","ICICIBANK.NS","INFY.NS","SBIN.NS"]

# =============================
# SCANNER
# =============================
def run_scanner(tickers):
    results = []

    try:
        data = yf.download(tickers, period="5d", interval="5m", group_by='ticker', progress=False)
    except Exception as e:
        st.error(f"Data fetch error: {e}")
        return pd.DataFrame()

    for t in tickers:
        try:
            # SAFE access
            if len(tickers) == 1:
                df = data
            else:
                if t not in data:
                    continue
                df = data[t]

            df = df.dropna()

            result = analyze_stock(df)
            if result is None:
                continue

            df, res, sup, vol_ratio, ai_view = result
            last = df.iloc[-1]

            ltp = round(last['Close'], 2)
            rsi = round(last['RSI'], 1)

            trend = "UPTREND" if last['EMA20'] > last['EMA50'] else "DOWNTREND"

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

        except Exception as e:
            st.warning(f"{t} error: {e}")
            continue

    return pd.DataFrame(results)

# =============================
# UI
# =============================
st.title("🔥 NSE Intraday Scanner (Fixed Version)")

df = run_scanner(stocks)

if not df.empty:
    st.dataframe(df, use_container_width=True)
    st.write(f"⏰ Updated: {pd.Timestamp.now().strftime('%H:%M:%S')}")
else:
    st.warning("No data / No signals found")
