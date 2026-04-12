import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from streamlit_autorefresh import st_autorefresh

# =============================
# PAGE CONFIG + AUTO REFRESH
# =============================
st.set_page_config(page_title="🔥 NSE AI Scanner (Big Movers + Big Player)", layout="wide")
st_autorefresh(interval=20000, key="refresh")

# =============================
# NSE SECTORS
# =============================
sectors = {
    "Nifty 50": ["RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS"],
    "Banking": ["SBIN.NS","HDFCBANK.NS","ICICIBANK.NS","AXISBANK.NS","KOTAKBANK.NS","PNB.NS"],
    "IT": ["INFY.NS","TCS.NS","WIPRO.NS","HCLTECH.NS","TECHM.NS"],
    "Auto": ["TATAMOTORS.NS","MARUTI.NS","M&M.NS","BAJAJ-AUTO.NS","HEROMOTOCO.NS"],
    "Pharma": ["SUNPHARMA.NS","DRREDDY.NS","CIPLA.NS","DIVISLAB.NS"],
    "FMCG": ["HINDUNILVR.NS","ITC.NS","NESTLEIND.NS","BRITANNIA.NS"],
    "Energy": ["RELIANCE.NS","ONGC.NS","BPCL.NS","IOC.NS"],
    "Metal": ["TATASTEEL.NS","JSWSTEEL.NS","HINDALCO.NS","COALINDIA.NS"]
}

# =============================
# SIDEBAR
# =============================
with st.sidebar:
    st.header("📊 Select NSE Sector")
    sector_name = st.selectbox("Sector", list(sectors.keys()))
    st.header("📌 Top 10 Big Movers")
    show_big = st.checkbox("Show Top 10 Movers Across All Sectors")

# =============================
# COLOR FUNCTIONS
# =============================
def color_signal(val):
    if "BUY" in str(val):
        return "background-color: green; color: white"
    elif "SELL" in str(val):
        return "background-color: red; color: white"
    elif "Big Buyer" in str(val):
        return "background-color: orange; color: white"
    elif "Big Seller" in str(val):
        return "background-color: purple; color: white"
    return ""

def color_trend(val):
    if val == "UP":
        return "background-color: green; color: white"
    elif val == "DOWN":
        return "background-color: red; color: white"
    return ""

# =============================
# AI ANALYSIS FUNCTION
# =============================
def analyze(df):
    if df is None or len(df) < 40:
        return None
    df = df.copy()
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    df['VWAP'] = (df['Close']*df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-9)
    delta = df['Close'].diff()
    gain = (delta.where(delta>0,0)).rolling(14).mean()
    loss = (-delta.where(delta<0,0)).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100/(1+rs))
    df['Target'] = np.where(df['Close'].shift(-1) > df['Close'], 1, 0)
    df.dropna(inplace=True)
    if len(df) < 10:
        return None
    features = ['EMA20','EMA50','RSI','VWAP']
    X = df[features]
    y = df['Target']
    X_train, X_test, y_train, y_test = train_test_split(X,y,test_size=0.2,shuffle=False)
    model = RandomForestClassifier(n_estimators=50,max_depth=5,random_state=42)
    model.fit(X_train,y_train)
    acc = round(model.score(X_test,y_test)*100,2)
    pred = model.predict(X.iloc[[-1]])[0]
    ai_signal = "BUY" if pred==1 else "SELL"
    avg_vol = df['Volume'].rolling(20).mean().iloc[-1]
    vol_ratio = df['Volume'].iloc[-1]/avg_vol if avg_vol>0 else 1
    return df, vol_ratio, ai_signal, acc

# =============================
# RUN SCANNER
# =============================
def run_scanner(tickers):
    results = []
    try:
        data = yf.download(tickers, period="5d", interval="5m", group_by='ticker', progress=False)
    except Exception as e:
        return pd.DataFrame()

    for s in tickers:
        try:
            df = data.copy() if len(tickers) == 1 else data[s].copy()
            df = df.dropna()
            if df.empty:
                continue
            analysis = analyze(df)
            if analysis:
                df, vol_ratio, ai_signal, acc = analysis
                trend = "UP" if ai_signal == "BUY" else "DOWN"
                results.append({
                    "Stock": s,
                    "Signal": ai_signal,
                    "Trend": trend,
                    "Vol Ratio": round(vol_ratio, 2),
                    "AI Acc": acc
                })
        except Exception as e:
            continue

    return pd.DataFrame(results)
