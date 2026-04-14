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

st.title("🔥 PRO NSE AI SCANNER (AI + MACD + SUPER TREND + OPTIONS)")

# =============================
# SECTORS
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
# ANALYSIS ENGINE (UPGRADED)
# =============================
def analyze(df):

    if df is None or len(df) < 60:
        return None

    df = df.copy()

    # ================= EMA =================
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    # ================= RSI =================
    delta = df['Close'].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))

    # ================= VWAP =================
    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-9)

    # ================= MACD =================
    df['EMA12'] = df['Close'].ewm(span=12).mean()
    df['EMA26'] = df['Close'].ewm(span=26).mean()
    df['MACD'] = df['EMA12'] - df['EMA26']
    df['Signal_Line'] = df['MACD'].ewm(span=9).mean()

    # ================= SUPER TREND =================
    hl2 = (df['High'] + df['Low']) / 2
    atr = (df['High'] - df['Low']).rolling(10).mean()
    df['UpperBand'] = hl2 + (2 * atr)
    df['LowerBand'] = hl2 - (2 * atr)

    df.dropna(inplace=True)

    # ================= AI TARGET =================
    df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
    df.dropna(inplace=True)

    features = ['EMA20','EMA50','RSI','VWAP','MACD']
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

    macd_buy = df['MACD'].iloc[-1] > df['Signal_Line'].iloc[-1]
    st_buy = price > df['LowerBand'].iloc[-1]

    # ================= SIGNAL =================
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

    # ================= BIG PLAYER =================
    avg_vol = df['Volume'].rolling(20).mean().iloc[-1]
    vol_ratio = df['Volume'].iloc[-1] / (avg_vol + 1e-9)

    if vol_ratio > 2:
        big = "🔥 BIG BUYER"
    elif vol_ratio < 0.5:
        big = "🔻 BIG SELLER"
    else:
        big = ""

    # ================= SCORE =================
    score = 0
    if "STRONG" in signal:
        score += 4
    if "BUY" in signal:
        score += 2
    if big == "🔥 BIG BUYER":
        score += 2
    if big == "🔻 BIG SELLER":
        score += 2

    # ================= CONFIDENCE FILTER =================
    confidence = 0
    if macd_buy: confidence += 20
    if st_buy: confidence += 20
    if rsi < 60: confidence += 20
    if score >= 6: confidence += 20
    if vol_ratio > 1.5: confidence += 20

    if confidence >= 80:
        final_signal = "🔥 HIGH PROBABILITY TRADE"
    elif confidence >= 60:
        final_signal = "⚡ WATCH"
    else:
        final_signal = "❌ AVOID"

    # ================= SUPPORT / RESISTANCE =================
    support = df['Low'].tail(40).min()
    resistance = df['High'].tail(40).max()

    # ================= ENTRY =================
    entry = round(price,2)

    # ================= OPTIONS SIGNAL =================
    if "STRONG BUY" in signal and macd_buy:
        option_signal = "🟢 CALL BUY (CE)"
    elif "STRONG SELL" in signal and not macd_buy:
        option_signal = "🔴 PUT BUY (PE)"
    else:
        option_signal = "⚪ NO TRADE"

    return df, signal, big, entry, final_signal, option_signal, score, support, resistance

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

            df, signal, big, entry, final_signal, option_signal, score, support, resistance = out

            price = df['Close'].iloc[-1]
            trend = "UP" if price > df['EMA50'].iloc[-1] else "DOWN"

            results.append({
                "Stock": stock,
                "Price": round(price,2),
                "Signal": signal,
                "Trend": trend,
                "Big Player": big,
                "Entry": entry,
                "Final Signal": final_signal,
                "Options": option_signal,
                "Score": score,
                "Support": round(support,2),
                "Resistance": round(resistance,2),
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

st.subheader("🔥 TOP TRADES (HIGH PROBABILITY)")
st.dataframe(df[df["Score"] >= 6], use_container_width=True)

st.download_button("⬇ Download CSV", df.to_csv(index=False), "scanner.csv")

st.subheader("📈 CHART")

if not df.empty:
    stock = st.selectbox("Select Stock", df["Stock"])
    data = get_data([stock])

    if data is not None:
        st.line_chart(data[stock]["Close"])
