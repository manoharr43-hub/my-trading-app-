import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier

# =============================
# PAGE CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI Scanner FINAL", layout="wide")

# =============================
# MODE
# =============================
st.sidebar.title("⚙️ Mode")

mode = st.sidebar.radio("Select Mode", ["🔴 Live", "📊 Backtest"])

if mode == "📊 Backtest":
    days = st.sidebar.selectbox("Period", ["5d","7d","1mo","3mo"])
    interval = st.sidebar.selectbox("Interval", ["5m","15m","30m","1h"])
else:
    days = "1d"
    interval = "5m"

# =============================
# STOCK LIST
# =============================
sectors = {
    "Nifty 50": ["RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS"],
    "Banking": ["SBIN.NS","HDFCBANK.NS","ICICIBANK.NS","AXISBANK.NS","KOTAKBANK.NS","PNB.NS"],
    "IT": ["INFY.NS","TCS.NS","WIPRO.NS","HCLTECH.NS","TECHM.NS"],
    "Auto": ["MARUTI.NS","M&M.NS","BAJAJ-AUTO.NS","HEROMOTOCO.NS"],
}

# =============================
# AI ANALYSIS
# =============================
def analyze(df):
    if len(df) < 40:
        return None

    df = df.copy()
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
    df.dropna(inplace=True)

    if len(df) < 10:
        return None

    X = df[['EMA20','EMA50']]
    y = df['Target']

    model = RandomForestClassifier(n_estimators=20)
    model.fit(X,y)

    pred = model.predict(X.iloc[[-1]])[0]
    return "BUY" if pred==1 else "SELL"

# =============================
# SUPPORT / RESISTANCE
# =============================
def support_resistance(df):
    return round(df['Close'].tail(50).min(),2), round(df['Close'].tail(50).max(),2)

# =============================
# TRADE LEVELS
# =============================
def trade_levels(price,support,resistance,signal):

    if signal=="BUY":
        entry = price+0.5
        sl = support
        t1 = entry+(price-support)
        t2 = entry+(price-support)*2
    else:
        entry = price-0.5
        sl = resistance
        t1 = entry-(resistance-price)
        t2 = entry-(resistance-price)*2

    return round(entry,2),round(sl,2),round(t1,2),round(t2,2)

# =============================
# CONFIRMATION (5m + 15m)
# =============================
def confirm_tf(ticker):
    try:
        df5 = yf.download(ticker, period="1d", interval="5m", progress=False)
        df15 = yf.download(ticker, period="1d", interval="15m", progress=False)

        s1 = analyze(df5)
        s2 = analyze(df15)

        return "✅" if s1 == s2 else "⚠️"
    except:
        return ""

# =============================
# SCANNER
# =============================
def run_scanner(tickers):

    results=[]

    for s in tickers:
        try:
            df = yf.download(s, period=days, interval=interval, progress=False)

            if df.empty:
                results.append({"Ticker":s,"Signal":"NO DATA"})
                continue

            price = round(df['Close'].iloc[-1],2)
            signal = analyze(df)

            support,resistance = support_resistance(df)
            entry,sl,t1,t2 = trade_levels(price,support,resistance,signal if signal else "SELL")

            time = df.index[-1]
            confirm = confirm_tf(s)

            results.append({
                "Ticker":s,
                "Price":price,
                "Time":time,
                "Signal":signal if signal else "NO DATA",
                "Support":support,
                "Resistance":resistance,
                "Entry":entry,
                "Stoploss":sl,
                "Target1":t1,
                "Target2":t2,
                "Confirm":confirm
            })

        except:
            results.append({"Ticker":s,"Signal":"ERROR"})

    return pd.DataFrame(results)

# =============================
# LIVE DISPLAY (OLD FORMAT)
# =============================
def show_live(df):
    st.subheader("📡 Live Market")

    if df.empty:
        st.warning("No Data")
        return

    d = df.copy()

    d['Signal'] = d['Signal'].apply(
        lambda x: "🟢 BUY" if x=="BUY" else ("🔴 SELL" if x=="SELL" else x)
    )

    st.dataframe(
        d[[
            "Ticker","Price","Signal",
            "Support","Resistance",
            "Entry","Stoploss","Target1","Target2"
        ]],
        use_container_width=True
    )

# =============================
# BACKTEST DISPLAY
# =============================
def show_backtest(df):
    st.subheader("📊 Backtest Data")

    if df.empty:
        st.warning("No Data")
        return

    d = df.copy()

    d['Signal'] = d['Signal'].apply(
        lambda x: "🟢 BUY" if x=="BUY" else ("🔴 SELL" if x=="SELL" else x)
    )

    d['Time'] = pd.to_datetime(d['Time'], errors='coerce').dt.strftime('%d-%m %H:%M')

    st.dataframe(
        d[[
            "Ticker","Time","Signal","Confirm",
            "Price","Support","Resistance",
            "Entry","Stoploss","Target1","Target2"
        ]],
        use_container_width=True
    )

# =============================
# MAIN UI
# =============================
st.title("🔥 NSE AI Scanner FINAL")

all_stocks = [t for sec in sectors.values() for t in sec]

if st.button("🚀 Run Scanner"):

    df = run_scanner(all_stocks)

    if mode == "🔴 Live":
        show_live(df)
    else:
        show_backtest(df)

    st.write("Total Stocks:", len(df))
