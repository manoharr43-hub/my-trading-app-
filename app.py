import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from streamlit_autorefresh import st_autorefresh

# =============================
# PAGE CONFIG
# =============================
st.set_page_config(page_title="🔥 PRO NSE AI SCANNER", layout="wide")
st_autorefresh(interval=5000, key="refresh")

st.title("🔥 PRO NSE AI SCANNER (Ultra Smart AI)")

# =============================
# STOCK LIST
# =============================
sectors = {
    "Nifty 50": ["RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS"],
    "Banking": ["SBIN.NS","AXISBANK.NS","KOTAKBANK.NS","PNB.NS"],
    "IT": ["WIPRO.NS","HCLTECH.NS"],
    "Auto": ["MARUTI.NS","M&M.NS","BAJAJ-AUTO.NS"],
    "Pharma": ["SUNPHARMA.NS","DRREDDY.NS","CIPLA.NS"],
    "Energy": ["ONGC.NS","IOC.NS"],
}

all_stocks = sorted(list(set([s for sec in sectors.values() for s in sec])))

# =============================
# DATA
# =============================
@st.cache_data(ttl=120)
def get_data(tickers):
    try:
        return yf.download(
            tickers,
            period="15d",
            interval="5m",
            group_by="ticker",
            threads=True,
            progress=False
        )
    except:
        return None

# =============================
# MODEL
# =============================
@st.cache_resource
def train_model(X, y):
    model = RandomForestClassifier(n_estimators=60, max_depth=5)
    model.fit(X, y)
    return model

# =============================
# ANALYSIS
# =============================
def analyze(df):

    if df is None or len(df) < 60:
        return None

    df = df.copy()

    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    delta = df['Close'].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()

    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))

    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-9)

    df.dropna(inplace=True)

    df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
    df.dropna(inplace=True)

    features = ['EMA20','EMA50','RSI','VWAP']

    X = df[features]
    y = df['Target']

    if len(X) < 30:
        return None

    model = train_model(X, y)
    pred = model.predict(X.iloc[[-1]])[0]

    price = df['Close'].iloc[-1]
    ema20 = df['EMA20'].iloc[-1]
    rsi = df['RSI'].iloc[-1]

    if pred == 1 and price > ema20 and rsi < 60:
        signal = "BUY"
    elif pred == 0 and price < ema20 and rsi > 40:
        signal = "SELL"
    else:
        signal = "SIDEWAYS"

    avg_vol = df['Volume'].rolling(20).mean().iloc[-1]
    vol_ratio = df['Volume'].iloc[-1] / avg_vol if avg_vol > 0 else 1

    if vol_ratio > 1.8:
        big = "Big Buyer"
    elif vol_ratio < 0.6:
        big = "Big Seller"
    else:
        big = ""

    return df, signal, big

# =============================
# LEVELS
# =============================
def levels(df):
    support = df['Low'].tail(40).min()
    resistance = df['High'].tail(40).max()
    return round(support,2), round(resistance,2)

# =============================
# TRADE
# =============================
def trade(price, support, resistance, signal):
    sl = round(price * 0.985, 2)

    if signal == "BUY":
        t1 = round(price + (resistance - support)*0.5,2)
        t2 = resistance
    elif signal == "SELL":
        t1 = round(price - (resistance - support)*0.5,2)
        t2 = support
    else:
        t1, t2 = "-", "-"

    return sl, t1, t2

# =============================
# STYLE FIX (IMPORTANT)
# =============================
def highlight(row):
    if row["Signal"] == "BUY":
        return ['background-color: #1E88E5; color: white'] * len(row)
    elif row["Signal"] == "SELL":
        return ['background-color: #E53935; color: white'] * len(row)
    return [''] * len(row)

# =============================
# SCANNER
# =============================
def scanner():

    results = []
    data = get_data(all_stocks)

    if data is None:
        return pd.DataFrame()

    for stock in all_stocks:

        try:
            df = data[stock].dropna()
            out = analyze(df)

            if out is None:
                continue

            df, signal, big = out

            price = round(df['Close'].iloc[-1],2)
            support, resistance = levels(df)
            sl, t1, t2 = trade(price, support, resistance, signal)

            trend = "UP" if price > df['EMA50'].iloc[-1] else "DOWN"

            score = 0
            if signal == "BUY":
                score += 2
                if trend == "UP":
                    score += 1
                if big == "Big Buyer":
                    score += 2

            elif signal == "SELL":
                score += 2
                if trend == "DOWN":
                    score += 1
                if big == "Big Seller":
                    score += 2

            results.append({
                "Stock": stock,
                "Price": price,
                "Signal": signal,
                "Trend": trend,
                "Support": support,
                "Resistance": resistance,
                "SL": sl,
                "T1": t1,
                "T2": t2,
                "Volume": big,
                "Score": score
            })

        except:
            continue

    return pd.DataFrame(results).sort_values(by="Score", ascending=False)

# =============================
# UI (STYLE FIXED SAFE)
# =============================
df = scanner()

tabs = st.tabs(list(sectors.keys()))

for i, sec in enumerate(sectors.keys()):
    with tabs[i]:
        sector_df = df[df["Stock"].isin(sectors[sec])]

        if not sector_df.empty:
            st.dataframe(
                sector_df.style.apply(highlight, axis=1),
                use_container_width=True
            )
        else:
            st.write("No data")

# =============================
# TOP TRADES
# =============================
st.subheader("🔥 TOP TRADES")

top = df[df["Score"] >= 3]

if not top.empty:
    st.dataframe(top.style.apply(highlight, axis=1), use_container_width=True)

# =============================
# DOWNLOAD
# =============================
st.download_button("⬇ Download CSV", df.to_csv(index=False), "scanner.csv")

# =============================
# CHART
# =============================
st.subheader("📈 Chart")

if not df.empty:
    stock = st.selectbox("Select Stock", df["Stock"])

    data = get_data([stock])
    if data is not None:
        chart_df = data[stock].dropna()
        st.line_chart(chart_df["Close"])
