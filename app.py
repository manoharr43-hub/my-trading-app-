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

st.title("🔥 PRO NSE AI SCANNER (FULL UPGRADE VERSION)")

# =============================
# SECTORS
# =============================
sectors = {
    "Nifty 50": ["RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS"],
    "Banking": ["SBIN.NS","AXISBANK.NS","KOTAKBANK.NS","PNB.NS"],
    "IT": ["WIPRO.NS","HCLTECH.NS","TECHM.NS"],
    "Auto": ["MARUTI.NS","M&M.NS","TATAMOTORS.NS"],
    "Pharma": ["SUNPHARMA.NS","DRREDDY.NS","CIPLA.NS"],
    "Energy": ["ONGC.NS","IOC.NS"],
    "FMCG": ["ITC.NS","NESTLEIND.NS"],
    "Metals": ["TATASTEEL.NS","JSWSTEEL.NS"],
    "Power": ["NTPC.NS","POWERGRID.NS"],
    "Finance": ["BAJFINANCE.NS","BAJAJFINSV.NS"]
}

selected_sector = st.selectbox("📊 Select Sector", list(sectors.keys()))
stocks_to_scan = sectors[selected_sector]

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
# ANALYSIS ENGINE
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

    # AI Target
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
    # SUPPORT / RESISTANCE
    # =============================
    support = df['Low'].tail(40).min()
    resistance = df['High'].tail(40).max()

    near_support = price <= support * 1.02
    near_resistance = price >= resistance * 0.98

    # =============================
    # BIG PLAYER
    # =============================
    avg_vol = df['Volume'].rolling(20).mean().iloc[-1]
    vol_ratio = df['Volume'].iloc[-1] / (avg_vol + 1e-9)

    if vol_ratio > 2:
        big = "🔥 BIG BUYER"
    elif vol_ratio < 0.5:
        big = "🔻 BIG SELLER"
    else:
        big = ""

    # =============================
    # 90% FILTER
    # =============================
    confidence = 0

    if price > ema20 > ema50:
        confidence += 20
    if 40 < rsi < 60:
        confidence += 15
    if macd > signal:
        confidence += 20
    if pred == 1:
        confidence += 20
    if vol_ratio > 1.5:
        confidence += 15
    if near_support or near_resistance:
        confidence += 10

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

    # =============================
    # ENTRY + STOPLOSS
    # =============================
    entry = round(price,2)

    if "BUY" in signal_text:
        stoploss = round(support,2)
    else:
        stoploss = round(resistance,2)

    return final, signal_text, confidence, price, support, resistance, big, entry, stoploss

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

            final, signal_text, confidence, price, support, resistance, big, entry, stoploss = out
            winrate = backtest(df)

            results.append({
                "Stock": stock,
                "Price": round(price,2),
                "Signal": signal_text,
                "Confidence": confidence,
                "Final": final,
                "Big Player": big,
                "Support": round(support,2),
                "Resistance": round(resistance,2),
                "Entry": entry,
                "Stoploss": stoploss,
                "WinRate%": winrate
            })

        except:
            continue

    result_df = pd.DataFrame(results).sort_values(by="Confidence", ascending=False)

    # =============================
    # UI
    # =============================
    st.subheader(f"🔥 {selected_sector} TOP TRADES")
    st.dataframe(result_df, use_container_width=True)

    st.subheader("🔥 HIGH PROBABILITY ONLY")
    st.dataframe(result_df[result_df["Confidence"] >= 85], use_container_width=True)

    st.subheader("📈 CHART")
    stock = st.selectbox("Select Stock", result_df["Stock"])
    st.line_chart(data[stock]["Close"])

    st.subheader("📊 PERFORMANCE")
    st.write("Avg WinRate:", round(result_df["WinRate%"].mean(),2))
    st.write("Top Stock:", result_df.iloc[0]["Stock"])
