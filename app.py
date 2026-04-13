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
st.set_page_config(page_title="🔥 PRO NSE AI SCANNER", layout="wide")
st_autorefresh(interval=5000, key="refresh")

st.title("🔥 PRO NSE AI SCANNER (Smart Entry/Exit + AI + Filters)")

# =============================
# NSE STOCK LIST
# =============================
sectors = {
    "Nifty 50": ["RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS"],
    "Banking": ["SBIN.NS","AXISBANK.NS","KOTAKBANK.NS","PNB.NS"],
    "IT": ["INFY.NS","TCS.NS","WIPRO.NS","HCLTECH.NS"],
    "Auto": ["MARUTI.NS","M&M.NS","BAJAJ-AUTO.NS"],
    "Pharma": ["SUNPHARMA.NS","DRREDDY.NS","CIPLA.NS"],
    "Energy": ["RELIANCE.NS","ONGC.NS","IOC.NS"],
}
all_stocks = list(set([s for sec in sectors.values() for s in sec]))

# =============================
# CACHE DATA
# =============================
@st.cache_data(ttl=60)
def get_data(tickers):
    return yf.download(tickers, period="30d", interval="5m", group_by='ticker', progress=False)

@st.cache_resource
def train_model(X, y):
    model = RandomForestClassifier(n_estimators=80, max_depth=6, random_state=42)
    model.fit(X, y)
    return model

# =============================
# ANALYSIS FUNCTION
# =============================
def analyze(df):
    if df is None or len(df) < 50:
        return None
    df = df.copy()

    # Indicators
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    df['EMA12'] = df['Close'].ewm(span=12).mean()
    df['EMA26'] = df['Close'].ewm(span=26).mean()
    df['MACD'] = df['EMA12'] - df['EMA26']

    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))

    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-9)

    # ✅ Corrected line (bracket closed properly)
    df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)

    df.dropna(inplace=True)

    if len(df) < 20:
        return None

    features = ['EMA20','EMA50','RSI','VWAP','MACD']
    X = df[features]
    y = df['Target']

    # ✅ Corrected line (bracket closed properly)
    X_train, _, y_train, _ = train_test_split(X, y, test_size=0.2, shuffle=False)
    model = train_model(X_train, y_train)
    pred = model.predict(X.iloc[[-1]])[0]

    # SMART SIGNAL
    if pred == 1 and df['RSI'].iloc[-1] < 65 and df['Close'].iloc[-1] > df['EMA20'].iloc[-1]:
        signal = "BUY"
    elif pred == 0 and df['RSI'].iloc[-1] > 35 and df['Close'].iloc[-1] < df['EMA20'].iloc[-1]:
        signal = "SELL"
    else:
        signal = "SIDEWAYS"

    # Big Player
    avg_vol = df['Volume'].rolling(20).mean().iloc[-1]
    vol_ratio = df['Volume'].iloc[-1] / avg_vol if avg_vol > 0 else 1
    if vol_ratio > 2:
        big = "Big Buyer"
    elif vol_ratio < 0.5:
        big = "Big Seller"
    else:
        big = ""

    return df, signal, big

# =============================
# SUPPORT / RESISTANCE
# =============================
def levels(df):
    support = round(df['Low'].tail(50).min(),2)
    resistance = round(df['High'].tail(50).max(),2)
    return support, resistance

# =================
