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
    show_movers = st.checkbox("Show Top 10 Movers Across All Sectors")

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
# GET INTRADAY MOVERS (SAFE)
# =============================
def get_intraday_movers(sectors):
    movers = []
    for sector, tickers in sectors.items():
        for s in tickers:
            try:
                df = yf.download(s, period="1d", interval="5m", progress=False)
                if df.empty or len(df) < 2:
                    continue
                open_price = df['Close'].iloc[0]
                last_price = df['Close'].iloc[-1]
                change_pct = ((last_price - open_price) / open_price) * 100
                movers.append({"Stock": s, "Change %": round(change_pct, 2)})
            except Exception:
                continue

    if not movers:
        return pd.DataFrame(columns=["Stock","Change %"])

    df_movers = pd.DataFrame(movers)
    df_movers["Change %"] = pd.to_numeric(df_movers["Change %"], errors="coerce").fillna(0)

    return df_movers.sort_values(by="Change %", ascending=False, na_position="last").head(10).reset_index(drop=True)

# =============================
# UI
# =============================
if show_movers:
    st.subheader("🚀 Top Intraday Movers")
    movers = get_intraday_movers(sectors)
    if not movers.empty:
        st.dataframe(movers, use_container_width=True)
    else:
        st.info("No movers data available (Market Closed)")
