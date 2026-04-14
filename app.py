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

st.title("🔥 PRO NSE AI SCANNER (Smart Entry/Exit + AI + Filters + SuperTrend)")

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

# =============================
# CACHE MODEL
# =============================
@st.cache_resource
def train_model(X, y):
    model = RandomForestClassifier(n_estimators=80, max_depth=6, random_state=42)
    model.fit(X, y)
    return model

# =============================
# SUPER TREND FUNCTION
# =============================
def add_supertrend(df, period=10, multiplier=3):
    hl2 = (df['High'] + df['Low']) / 2
    atr = (df['High'] - df['Low']).rolling(period).mean()
    df['UpperBand'] = hl2 + (multiplier * atr)
    df['LowerBand'] = hl2 - (multiplier * atr)
    df['SuperTrend'] = np.where(df['Close'] > df['UpperBand'], df['LowerBand'], df['UpperBand'])
    df['ST_Trend'] = np.where(df['Close'] > df['SuperTrend'], "UP", "DOWN")
    return df

# =============================
# ANALYSIS
# =============================
def analyze(df):
    if df is None or len(df) < 50:
        return None

    df = df.copy()
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

    df['ATR'] = (df['High'] - df['Low']).rolling(14).mean()
    df['BB_upper'] = df['Close'].rolling(20).mean() + 2*df['Close'].rolling(20).std()
    df['BB_lower'] = df['Close'].rolling(20).mean() - 2*df['Close'].rolling(20).std()

    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-9)
    df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
    df.dropna(inplace=True)

    df = add_supertrend(df)

    if len(df) < 20:
        return None

    features = ['EMA20','EMA50','RSI','VWAP','MACD','ATR']
    X = df[features]
    y = df['Target']

    X_train, _, y_train, _ = train_test_split(X, y, test_size=0.2, shuffle=False)
    model = train_model(X_train, y_train)
    pred = model.predict(X.iloc[[-1]])[0]

    if pred == 1 and df['RSI'].iloc[-1] < 65 and df['Close'].iloc[-1] > df['EMA20'].iloc[-1]:
        signal = "BUY"
    elif pred == 0 and df['RSI'].iloc[-1] > 35 and df['Close'].iloc[-1] < df['EMA20'].iloc[-1]:
        signal = "SELL"
    else:
        signal = "SIDEWAYS"

    avg_vol = df['Volume'].rolling(20).mean().iloc[-1]
    vol_ratio = df['Volume'].iloc[-1] / avg_vol if avg_vol > 0 else 1

    if vol_ratio > 2:
        big = "Big Buyer"
    elif vol_ratio < 0.5:
        big = "Big Seller"
    else:
        big = ""

    return df, signal, big
