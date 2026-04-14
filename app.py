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

st.title("🔥 PRO NSE AI SCANNER (STRONG ENTRY + BIG MONEY + AI)")

# =============================
# NSE SECTORS (EXPANDED)
# =============================
sectors = {
    "Nifty 50": ["RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS"],
    "Banking": ["SBIN.NS","AXISBANK.NS","KOTAKBANK.NS","PNB.NS","BANKBARODA.NS","INDUSINDBK.NS"],
    "IT": ["WIPRO.NS","HCLTECH.NS","TECHM.NS","LTIM.NS"],
    "Auto": ["MARUTI.NS","M&M.NS","BAJAJ-AUTO.NS","TATAMOTORS.NS"],
    "Pharma": ["SUNPHARMA.NS","DRREDDY.NS","CIPLA.NS","LUPIN.NS"],
    "Energy": ["ONGC.NS","IOC.NS","RELIANCE.NS"],
    "FMCG": ["HINDUNILVR.NS","ITC.NS","NESTLEIND.NS"],
    "Metals": ["TATASTEEL.NS","JSWSTEEL.NS","HINDALCO.NS"],
}

all_stocks = sorted(list(set([s for sec in sectors.values() for s in sec])))

# =============================
# DATA
# =============================
@st.cache_data(ttl=120)
def get_data(tickers):
    try:
        return yf.download(tickers, period="15d", interval="5m", group_by="ticker", progress=False)
    except:
        return None

# =============================
# MODEL
# =============================
@st.cache_resource
def train_model(X, y):
    model = RandomForestClassifier(n_estimators=70, max_depth=6)
    model.fit(X, y)
    return model

# =============================
# ANALYSIS + BIG PLAYER FIX + STRONG SIGNAL
# =============================
def analyze(df):

    if df is None or len(df) < 60:
        return None

    df = df.copy()

    # Indicators
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    delta = df['Close'].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()

    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))

    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-9)

    df.dropna(inplace=True)

    # AI TARGET
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
    ema50 = df['EMA50'].iloc[-1]
    rsi = df['RSI'].iloc[-1]

    # =============================
    # 🔥 STRONG SIGNAL LOGIC (NEW)
    # =============================
    if pred == 1 and price > ema20 and ema20 > ema50 and rsi < 60:
        signal = "🟢 STRONG BUY"
    elif pred == 0 and price < ema20 and ema20 < ema50 and rsi > 40:
        signal = "🔴 STRONG SELL"
    elif price > ema20:
        signal = "BUY"
    elif price < ema20:
        signal = "SELL"
    else:
        signal = "SIDEWAYS"

    # =============================
    # 🔥 BIG PLAYER FIX (REAL VOLUME SPIKE)
    # =============================
    avg_vol = df['Volume'].rolling(20).mean().iloc[-1]
    vol_ratio = df['Volume'].iloc[-1] / (avg_vol + 1e-9)

    if vol_ratio > 2.0:
        big = "🔥 BIG BUYER"
    elif vol_ratio < 0.5:
        big = "🔻 BIG SELLER"
    else:
        big = ""

    # =============================
    # ENTRY POINT CALCULATION
    # =============================
    entry_zone = round(price,2)

    if signal in ["🟢 STRONG BUY","BUY"]:
        entry_note = "📍 BUY ZONE (Near EMA Support)"
    elif signal in ["🔴 STRONG SELL","SELL"]:
        entry_note = "📍 SELL ZONE (Near EMA Resistance)"
    else:
        entry_note = "WAIT"

    return df, signal, big, entry_zone, entry_note

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

    if "BUY" in signal:
        t1 = round(price + (resistance - support)*0.5,2)
        t2 = resistance
    elif "SELL" in signal:
        t1 = round(price - (resistance - support)*0.5,2)
        t2 = support
    else:
        t1, t2 = "-", "-"

    return sl, t1, t2

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

            df, signal, big, entry, note = out

            price = round(df['Close'].iloc[-1],2)
            support, resistance = levels(df)
            sl, t1, t2 = trade(price, support, resistance, signal)

            trend = "UP" if price > df['EMA50'].iloc[-1] else "DOWN"

            score = 0

            if "STRONG BUY" in signal:
                score += 4
            if "STRONG SELL" in signal:
                score += 4

            if "BUY" in signal:
                score += 2
            if "SELL" in signal:
                score += 2

            if big == "🔥 BIG BUYER":
                score += 2
            if big == "🔻 BIG SELLER":
                score += 2

            results.append({
                "Stock": stock,
                "Price": price,
                "Signal": signal,
                "Trend": trend,
                "Big Player": big,
                "Entry": entry,
                "Entry Note": note,
                "Support": support,
                "Resistance": resistance,
                "SL": sl,
                "T1": t1,
                "T2": t2,
                "Score": score
            })

        except:
            continue

    return pd.DataFrame(results).sort_values(by="Score", ascending=False)

# =============================
# UI
# =============================
df = scanner()

tabs = st.tabs(list(sectors.keys()))

for i, sec in enumerate(sectors.keys()):
    with tabs[i]:
        st.dataframe(df[df["Stock"].isin(sectors[sec])], use_container_width=True)

# =============================
# TOP TRADES
# =============================
st.subheader("🔥 TOP STRONG TRADES")

top = df[df["Score"] >= 5]
st.dataframe(top, use_container_width=True)

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
        st.line_chart(data[stock]["Close"])
