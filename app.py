import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import datetime
from sklearn.ensemble import RandomForestClassifier
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="⚡ NSE Intraday AI PRO", layout="wide")
st_autorefresh(interval=20000, key="refresh")

# =============================
# CACHE (FAST DATA)
# =============================
@st.cache_data(ttl=30)
def get_data(stock, period, interval):
    return yf.download(stock, period=period, interval=interval, progress=False)

# =============================
# NSE STOCK LIST
# =============================
sectors = {
    "Nifty": ["RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS"],
    "Bank": ["SBIN.NS","AXISBANK.NS","KOTAKBANK.NS"],
    "IT": ["WIPRO.NS","HCLTECH.NS","TECHM.NS"],
    "Auto": ["TATAMOTORS.NS","MARUTI.NS","M&M.NS"],
}

# =============================
# SIDEBAR
# =============================
with st.sidebar:
    st.header("⚡ Settings")
    sector = st.selectbox("Select Sector", list(sectors.keys()))
    show_movers = st.checkbox("Show Movers")

# =============================
# MARKET TIME CHECK
# =============================
now = datetime.datetime.now().time()
if now < datetime.time(9,15) or now > datetime.time(15,30):
    st.warning("⚠ Market Closed (Data delay possible)")

# =============================
# ANALYSIS
# =============================
def analyze(df):
    if df is None or len(df) < 30:
        return None

    df = df.copy()

    df['EMA9'] = df['Close'].ewm(span=9).mean()
    df['EMA21'] = df['Close'].ewm(span=21).mean()

    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))

    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-9)

    df.dropna(inplace=True)

    if len(df) < 20:
        return None

    # AI
    df['Target'] = np.where(df['Close'].shift(-1) > df['Close'], 1, 0)
    features = ['EMA9','EMA21','RSI','VWAP']

    X = df[features]
    y = df['Target']

    model = RandomForestClassifier(n_estimators=100, max_depth=6)
    model.fit(X[:-1], y[:-1])

    pred = model.predict(X.iloc[[-1]])[0]
    ai = "BUY" if pred == 1 else "SELL"

    # Volume
    avg_vol = df['Volume'].rolling(10).mean().iloc[-1]
    vol = df['Volume'].iloc[-1] / avg_vol if avg_vol > 0 else 1

    last = df.iloc[-1]

    # Entry / SL / Target
    entry = last['Close']
    sl = entry * 0.995
    target = entry * 1.01

    return last, ai, vol, entry, sl, target

# =============================
# SCANNER
# =============================
def scanner(tickers):
    output = []

    for s in tickers:
        try:
            df = get_data(s, "1d", "5m")

            if df.empty:
                continue

            res = analyze(df)
            if res is None:
                continue

            last, ai, vol, entry, sl, target = res

            trend = "UP" if last['EMA9'] > last['EMA21'] else "DOWN"
            rsi = last['RSI']
            vwap = last['VWAP']
            price = last['Close']

            signal = "WAIT"

            if price > vwap and trend == "UP" and rsi > 60 and ai == "BUY":
                signal = "BUY"
                if vol > 2:
                    signal = "🔥 BIG BUY"

            elif price < vwap and trend == "DOWN" and rsi < 40 and ai == "SELL":
                signal = "SELL"
                if vol > 2:
                    signal = "🔥 BIG SELL"

            output.append({
                "Stock": s.replace(".NS",""),
                "Price": round(price,2),
                "Trend": trend,
                "RSI": round(rsi,1),
                "Vol Spike": round(vol,2),
                "AI": ai,
                "Signal": signal,
                "Entry": round(entry,2),
                "SL": round(sl,2),
                "Target": round(target,2)
            })

        except:
            continue

    df = pd.DataFrame(output)

    if not df.empty:
        df = df.sort_values(by="Vol Spike", ascending=False)

    return df

# =============================
# MOVERS
# =============================
def movers(all_sec):
    data = []

    for t in all_sec.values():
        for s in t:
            try:
                df = get_data(s, "1d", "15m")

                if len(df) < 2:
                    continue

                pct = ((df['Close'].iloc[-1] / df['Close'].iloc[0]) - 1) * 100

                data.append({
                    "Stock": s.replace(".NS",""),
                    "Change %": round(pct,2)
                })

            except:
                continue

    return pd.DataFrame(data).sort_values(by="Change %", ascending=False).head(10)

# =============================
# UI
# =============================
st.title("⚡ NSE INTRADAY AI PRO SCANNER")

data = scanner(sectors[sector])

if not data.empty:
    st.dataframe(data, use_container_width=True)

    stock = st.selectbox("Select Stock", data['Stock'])

    chart = get_data(stock+".NS", "1d", "5m")

    if not chart.empty:
        st.line_chart(chart['Close'])

else:
    st.warning("No signals now")

# Movers
if show_movers:
    st.subheader("🚀 Top Intraday Movers")

    mv = movers(sectors)

    if not mv.empty:
        st.dataframe(mv, use_container_width=True)
