import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from streamlit_autorefresh import st_autorefresh

# =============================
# PAGE CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI Scanner PRO", layout="wide")
st_autorefresh(interval=60000, key="refresh")

# =============================
# NSE SECTORS
# =============================
sectors = {
    "Nifty 50": ["RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS"],
    "Banking": ["SBIN.NS","HDFCBANK.NS","ICICIBANK.NS","AXISBANK.NS","KOTAKBANK.NS","PNB.NS"],
    "IT": ["INFY.NS","TCS.NS","WIPRO.NS","HCLTECH.NS","TECHM.NS"],
    "Auto": ["MARUTI.NS","M&M.NS","BAJAJ-AUTO.NS","HEROMOTOCO.NS"],
    "Pharma": ["SUNPHARMA.NS","DRREDDY.NS","CIPLA.NS","DIVISLAB.NS"],
    "FMCG": ["HINDUNILVR.NS","ITC.NS","NESTLEIND.NS","BRITANNIA.NS"],
    "Energy": ["RELIANCE.NS","ONGC.NS","BPCL.NS","IOC.NS"],
    "Metal": ["TATASTEEL.NS","JSWSTEEL.NS","HINDALCO.NS","COALINDIA.NS"]
}

# =============================
# AI ANALYSIS
# =============================
def analyze(df):
    if df is None or len(df) < 40:
        return None

    df = df.copy()

    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-9)

    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))

    df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)

    df.dropna(inplace=True)

    if len(df) < 10:
        return None

    X = df[['EMA20','EMA50','RSI','VWAP']]
    y = df['Target']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

    model = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
    model.fit(X_train, y_train)

    pred = model.predict(X.iloc[[-1]])[0]
    signal = "BUY" if pred == 1 else "SELL"

    avg_vol = df['Volume'].rolling(20).mean().iloc[-1]
    vol_ratio = df['Volume'].iloc[-1] / avg_vol if avg_vol > 0 else 1

    big_player = "Big Buyer" if vol_ratio > 2 else ("Big Seller" if vol_ratio < 0.5 else "")

    return df, signal, big_player

# =============================
# SUPPORT RESISTANCE
# =============================
def support_resistance(df):
    closes = df['Close'].tail(50)
    return round(closes.min(),2), round(closes.max(),2)

# =============================
# SMART TRADE LEVELS 🔥
# =============================
def trade_levels(price, support, resistance, signal):

    if signal == "BUY":
        risk = price - support
        entry = round(price + 0.5, 2)
        stoploss = round(support, 2)
        target1 = round(entry + risk, 2)
        target2 = round(entry + (risk * 2), 2)

    else:  # SELL
        risk = resistance - price
        entry = round(price - 0.5, 2)
        stoploss = round(resistance, 2)
        target1 = round(entry - risk, 2)
        target2 = round(entry - (risk * 2), 2)

    return entry, stoploss, target1, target2

# =============================
# SCANNER
# =============================
def run_scanner(tickers):

    results = []

    try:
        data = yf.download(tickers, period="5d", interval="5m", group_by='ticker', progress=False)
    except:
        return pd.DataFrame()

    for s in tickers:
        try:
            df = data.copy() if len(tickers) == 1 else data[s].copy()
            df = df.dropna()

            if df.empty or "Close" not in df.columns:
                continue

            result = analyze(df)
            if result is None:
                continue

            df, signal, big_player = result

            price = round(df['Close'].iloc[-1], 2)

            change_pct = ((df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0]) * 100
            trend = "UP" if change_pct > 0 else "DOWN"

            support, resistance = support_resistance(df)

            # ✅ NEW LOGIC
            entry, stoploss, target1, target2 = trade_levels(price, support, resistance, signal)

            results.append({
                "Ticker": s,
                "Price": price,
                "Signal": signal,
                "Trend": trend,
                "Support": support,
                "Resistance": resistance,
                "Entry": entry,
                "Stoploss": stoploss,
                "Target1": target1,
                "Target2": target2,
                "Big Player": big_player
            })

        except:
            continue

    return pd.DataFrame(results)

# =============================
# DISPLAY
# =============================
def show(df, title):
    st.subheader(title)

    if df.empty:
        st.warning("No Data")
        return

    df['Signal'] = df['Signal'].apply(lambda x: "🟢 BUY" if x=="BUY" else "🔴 SELL")
    df['Trend'] = df['Trend'].apply(lambda x: "🟢 UP" if x=="UP" else "🔴 DOWN")

    st.dataframe(df, use_container_width=True)

# =============================
# UI
# =============================
st.title("🔥 NSE AI Scanner PRO (Smart Entry/Exit/Target)")

if st.button("🚀 Run Scanner"):
    all_stocks = [t for sec in sectors.values() for t in sec]
    df = run_scanner(all_stocks)
    show(df, "📊 AI Trading Signals")
