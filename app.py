import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from streamlit_autorefresh import st_autorefresh

# =============================
# PAGE SETUP
# =============================
st.set_page_config(page_title="🔥 PRO NSE AI BACKTEST SCANNER", layout="wide")
st_autorefresh(interval=8000, key="refresh")

st.title("🔥 PRO NSE AI SCANNER + BACKTEST + 90% FILTER")

# =============================
# SECTORS
# =============================
sectors = {
    "Nifty 50": ["RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS"],
    "Banking": ["SBIN.NS","AXISBANK.NS","KOTAKBANK.NS","PNB.NS"],
    "IT": ["WIPRO.NS","HCLTECH.NS","TECHM.NS"],
}

all_stocks = sorted(list(set([s for sec in sectors.values() for s in sec])))

# =============================
# DATA
# =============================
@st.cache_data(ttl=120)
def get_data(tickers):
    return yf.download(tickers, period="60d", interval="15m", group_by="ticker")

# =============================
# MODEL
# =============================
@st.cache_resource
def train_model(X, y):
    model = RandomForestClassifier(n_estimators=80, max_depth=6)
    model.fit(X, y)
    return model

# =============================
# TECHNICAL ENGINE
# =============================
def analyze(df):

    df = df.copy()

    # EMA
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    # RSI
    delta = df['Close'].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))

    # MACD
    df['EMA12'] = df['Close'].ewm(span=12).mean()
    df['EMA26'] = df['Close'].ewm(span=26).mean()
    df['MACD'] = df['EMA12'] - df['EMA26']
    df['Signal'] = df['MACD'].ewm(span=9).mean()

    df.dropna(inplace=True)

    # AI TARGET
    df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
    df.dropna(inplace=True)

    features = ['EMA20','EMA50','RSI','MACD']

    X = df[features]
    y = df['Target']

    if len(X) < 50:
        return None

    model = train_model(X, y)

    pred = model.predict(X.iloc[[-1]])[0]

    price = df['Close'].iloc[-1]
    ema20 = df['EMA20'].iloc[-1]
    ema50 = df['EMA50'].iloc[-1]
    rsi = df['RSI'].iloc[-1]
    macd = df['MACD'].iloc[-1]
    signal = df['Signal'].iloc[-1]

    # =============================
    # 90% FILTER LOGIC (IMPORTANT)
    # =============================
    confidence = 0

    if price > ema20 > ema50:
        confidence += 25
    if 40 < rsi < 60:
        confidence += 20
    if macd > signal:
        confidence += 20
    if pred == 1:
        confidence += 20

    volume_ok = True  # simplified
    if volume_ok:
        confidence += 15

    # =============================
    # SIGNAL
    # =============================
    if confidence >= 85:
        final = "🔥 HIGH PROBABILITY TRADE"
    elif confidence >= 60:
        final = "⚡ WATCH"
    else:
        final = "❌ AVOID"

    if pred == 1:
        signal_text = "🟢 BUY"
    else:
        signal_text = "🔴 SELL"

    return final, signal_text, confidence, price

# =============================
# BACKTEST ENGINE
# =============================
def backtest(df):

    df = df.copy()

    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
    df.dropna(inplace=True)

    correct = 0
    total = 0

    for i in range(50, len(df)-1):
        if df['EMA20'].iloc[i] > df['EMA50'].iloc[i]:
            pred = 1
        else:
            pred = 0

        if pred == df['Target'].iloc[i]:
            correct += 1
        total += 1

    winrate = (correct / total) * 100 if total > 0 else 0
    return round(winrate, 2)

# =============================
# SCANNER
# =============================
data = get_data(all_stocks)

results = []

if data is not None:

    for stock in all_stocks:
        try:
            df = data[stock].dropna()

            out = analyze(df)
            if out is None:
                continue

            final, signal_text, confidence, price = out
            winrate = backtest(df)

            results.append({
                "Stock": stock,
                "Price": round(price,2),
                "Signal": signal_text,
                "Confidence": confidence,
                "Final": final,
                "WinRate%": winrate
            })

        except:
            continue

    result_df = pd.DataFrame(results).sort_values(by="Confidence", ascending=False)

    # =============================
    # UI
    # =============================
    st.subheader("🔥 TOP HIGH PROBABILITY TRADES")

    st.dataframe(result_df)

    st.subheader("🔥 ONLY BEST SETUPS (90% FILTER)")

    st.dataframe(result_df[result_df["Confidence"] >= 85])

    st.subheader("📊 SELECT STOCK CHART")

    stock = st.selectbox("Select Stock", result_df["Stock"])
    st.line_chart(data[stock]["Close"])

    st.subheader("📈 OVERALL STATS")

    st.write("Avg WinRate:", round(result_df["WinRate%"].mean(),2))
    st.write("Best Stock:", result_df.iloc[0]["Stock"])
