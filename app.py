import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier

st.set_page_config(page_title="🔥 NSE AI Scanner FINAL", layout="wide")

# =============================
# MODE
# =============================
mode = st.sidebar.radio("Mode", ["🔴 Live", "📊 Backtest"])

if mode == "📊 Backtest":
    days = st.sidebar.selectbox("Period", ["5d","7d","1mo"])
    interval = st.sidebar.selectbox("Interval", ["5m","15m"])
else:
    days = "1d"
    interval = "5m"

# =============================
# STOCKS
# =============================
stocks = ["RELIANCE.NS","TCS.NS","INFY.NS","SBIN.NS","HDFCBANK.NS",
          "ICICIBANK.NS","AXISBANK.NS","WIPRO.NS","MARUTI.NS"]

# =============================
# AI
# =============================
def analyze(df):
    if len(df) < 40:
        return None

    df = df.copy()
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
    df.dropna(inplace=True)

    X = df[['EMA20','EMA50']]
    y = df['Target']

    model = RandomForestClassifier(n_estimators=20)
    model.fit(X,y)

    pred = model.predict(X.iloc[[-1]])[0]
    return "BUY" if pred==1 else "SELL"

# =============================
# SUPPORT/RESISTANCE
# =============================
def sr(df):
    return df['Close'].tail(50).min(), df['Close'].tail(50).max()

# =============================
# TRADE LEVELS
# =============================
def trade(price,s,r,signal):
    if signal=="BUY":
        entry = price+0.5
        sl = s
        t1 = entry+(price-s)
        t2 = entry+(price-s)*2
    else:
        entry = price-0.5
        sl = r
        t1 = entry-(r-price)
        t2 = entry-(r-price)*2
    return round(entry,2),round(sl,2),round(t1,2),round(t2,2)

# =============================
# CONFIRMATION
# =============================
def confirm_tf(t):
    try:
        df5 = yf.download(t, period="1d", interval="5m", progress=False)
        df15 = yf.download(t, period="1d", interval="15m", progress=False)
        s1 = analyze(df5)
        s2 = analyze(df15)

        if s1==s2:
            return "✅ Strong"
        else:
            return "⚠️ Weak"
    except:
        return ""

# =============================
# SCANNER
# =============================
def run():

    data=[]

    for s in stocks:
        try:
            df = yf.download(s, period=days, interval=interval, progress=False)

            if df.empty:
                continue

            price = round(df['Close'].iloc[-1],2)
            signal = analyze(df)

            spt,res = sr(df)
            entry,sl,t1,t2 = trade(price,spt,res,signal if signal else "SELL")

            time = df.index[-1]

            confirm = confirm_tf(s)

            data.append({
                "Ticker":s,
                "Price":price,
                "Signal":signal,
                "Support":round(spt,2),
                "Resistance":round(res,2),
                "Entry":entry,
                "Stoploss":sl,
                "Target1":t1,
                "Target2":t2,
                "Confirm":confirm,
                "Time":time,
                "TF":interval   # 🔥 timeframe column
            })

        except:
            continue

    return pd.DataFrame(data)

# =============================
# FILTERS
# =============================
def top5(df):
    return df.head(5)

def high_accuracy(df):
    return df[df['Confirm']=="✅ Strong"]

# =============================
# UI
# =============================
st.title("🔥 NSE AI Scanner")

if st.button("🚀 Run Scanner"):

    df = run()

    if mode == "🔴 Live":

        st.subheader("📡 Live - All Stocks")
        st.dataframe(df[[
            "Ticker","Price","Signal",
            "Support","Resistance",
            "Entry","Stoploss","Target1","Target2"
        ]])

        st.subheader("⭐ Top 5 Trades")
        st.dataframe(top5(df)[[
            "Ticker","Price","Signal",
            "Entry","Stoploss","Target1","Target2"
        ]])

        st.subheader("🎯 High Accuracy")
        st.dataframe(high_accuracy(df)[[
            "Ticker","Price","Signal",
            "Entry","Stoploss","Target1","Target2"
        ]])

    else:
        st.subheader("📊 Backtest Report")

        df['Time'] = pd.to_datetime(df['Time']).dt.strftime('%d-%m %H:%M')

        st.dataframe(df[[
            "Ticker","Time","TF","Signal","Confirm",
            "Price","Entry","Stoploss","Target1","Target2"
        ]])
