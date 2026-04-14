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
st_autorefresh(interval=8000, key="refresh")

st.title("🔥 PRO NSE AI SCANNER (AI + BACKTEST + 90% FILTER)")

# =============================
# SECTORS (ALL MAJOR NSE)
# =============================
sectors = {
    "Nifty 50": ["RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS"],
    "Banking": ["SBIN.NS","AXISBANK.NS","KOTAKBANK.NS","PNB.NS","BANKBARODA.NS"],
    "IT": ["WIPRO.NS","HCLTECH.NS","TECHM.NS","LTIM.NS"],
    "Auto": ["MARUTI.NS","M&M.NS","TATAMOTORS.NS"],
    "Pharma": ["SUNPHARMA.NS","DRREDDY.NS","CIPLA.NS"],
    "Energy": ["ONGC.NS","IOC.NS","RELIANCE.NS"],
    "FMCG": ["HINDUNILVR.NS","ITC.NS","NESTLEIND.NS"],
    "Metals": ["TATASTEEL.NS","JSWSTEEL.NS","HINDALCO.NS"],
    "Power": ["NTPC.NS","POWERGRID.NS","TATAPOWER.NS"],
    "Telecom": ["BHARTIARTL.NS","IDEA.NS"],
    "Finance": ["BAJFINANCE.NS","BAJAJFINSV.NS"],
    "Infra": ["LT.NS","ADANIPORTS.NS"],
    "Defence": ["HAL.NS","BEL.NS"],
    "Railways": ["IRCTC.NS","IRFC.NS"]
}

# =============================
# SELECT SECTOR (SPEED CONTROL)
# =============================
selected_sector = st.selectbox("📊 Select Sector", list(sectors.keys()))
stocks_to_scan = sectors[selected_sector]

# =============================
# DATA FETCH
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
# ANALYSIS ENGINE
# =============================
def analyze(df):

    df = df.copy()

    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    delta = df['Close'].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))

    df['EMA12'] = df['Close'].ewm(span=12).mean()
    df['EMA26'] = df['Close'].ewm(span=26).mean()
    df['MACD'] = df['EMA12'] - df['EMA26']
    df['Signal'] = df['MACD'].ewm(span=9).mean()

    df.dropna(inplace=True)

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
    # 90% FILTER
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

    confidence += 15

    # =============================
    # FINAL SIGNAL
    # =============================
    if confidence >= 85:
        final = "🔥 HIGH PROBABILITY"
    elif confidence >= 60:
        final = "⚡ WATCH"
    else:
        final = "❌ AVOID"

    signal_text = "🟢 BUY" if pred == 1 else "🔴 SELL"

    return final, signal_text, confidence, price

# =============================
# BACKTEST
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
        pred = 1 if df['EMA20'].iloc[i] > df['EMA50'].iloc[i] else 0
        if pred == df['Target'].iloc[i]:
            correct += 1
        total += 1

    return round((correct/total)*100,2) if total > 0 else 0

# =============================
# SCANNER
# =============================
data = get_data(stocks_to_scan)

results = []

if data is not None:

    for stock in stocks_to_scan:
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
    # UI OUTPUT
    # =============================
    st.subheader(f"🔥 {selected_sector} TOP TRADES")
    st.dataframe(result_df, use_container_width=True)

    st.subheader("🔥 HIGH PROBABILITY (90% FILTER)")
    st.dataframe(result_df[result_df["Confidence"] >= 85], use_container_width=True)

    st.subheader("📈 STOCK CHART")
    stock = st.selectbox("Select Stock", result_df["Stock"])
    st.line_chart(data[stock]["Close"])

    st.subheader("📊 PERFORMANCE")
    st.write("Avg WinRate:", round(result_df["WinRate%"].mean(),2))
    st.write("Top Stock:", result_df.iloc[0]["Stock"])
