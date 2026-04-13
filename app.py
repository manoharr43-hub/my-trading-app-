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
st.set_page_config(page_title="🔥 NSE AI Scanner (Support + Resistance)", layout="wide")
st_autorefresh(interval=60000, key="refresh")  # auto refresh every 1 min

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
# SIDEBAR
# =============================
with st.sidebar:
    st.header("📊 Select NSE Sector")
    sector_name = st.selectbox("Sector", list(sectors.keys()))
    st.header("📌 Top 10 Big Movers")
    show_big = st.checkbox("Show Top 10 Movers Across All Sectors")
    st.header("🔎 Manual Symbol Entry")
    manual_symbol = st.text_input("Enter NSE Symbol (use .NS)", "")

# =============================
# AI ANALYSIS FUNCTION
# =============================
def analyze(df):
    if df is None or len(df)<40:
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
    df['Target'] = (df['Close'].shift(-1).values > df['Close'].values).astype(int)
    df.dropna(inplace=True)
    if len(df)<10:
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
# SUPPORT & RESISTANCE FUNCTION
# =============================
def support_resistance(df):
    closes = df['Close'].tail(50)  # last 50 candles
    support = round(closes.min(),2)
    resistance = round(closes.max(),2)
    return support, resistance

# =============================
# RUN SCANNER
# =============================
def run_scanner(tickers):
    results=[]
    try:
        data = yf.download(tickers, period="5d", interval="5m", group_by='ticker', progress=False)
    except:
        return pd.DataFrame()
    for s in tickers:
        try:
            df = data.copy() if len(tickers)==1 else data[s].copy()
            df = df.dropna()
            if df.empty or "Close" not in df.columns:
                continue
            df, vol_ratio, ai_signal, acc = analyze(df)
            if df is None:
                continue
            change_pct = ((df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0]) * 100
            trend = "UP" if change_pct>0 else "DOWN"
            big_player = "Big Buyer" if vol_ratio>2 else ("Big Seller" if vol_ratio<0.5 else "")
            support, resistance = support_resistance(df)
            results.append({
                "Ticker": s,
                "Price": round(df['Close'].iloc[-1],2),
                "Support": support,
                "Resistance": resistance,
                "Change %": round(change_pct,2),
                "Trend": trend,
                "AI Signal": ai_signal,
                "Accuracy %": acc,
                "Volume Ratio": round(vol_ratio,2),
                "Player": big_player
            })
        except Exception:
            continue
    return pd.DataFrame(results)

# =============================
# DISPLAY FUNCTION
# =============================
def show_table(df, title):
    st.subheader(title)
    if df.empty:
        st.warning("⚠️ No data found.")
    else:
        df_display = df.copy()
        df_display['AI Signal'] = df_display['AI Signal'].apply(
            lambda x: "🟢 BUY" if x=="BUY" else "🔴 SELL"
        )
        df_display['Trend'] = df_display['Trend'].apply(
            lambda x: "🟢 UP" if x
