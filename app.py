import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from sklearn.ensemble import RandomForestClassifier
from streamlit_autorefresh import st_autorefresh

# =============================
# PAGE CONFIG
# =============================
st.set_page_config(page_title="⚡ ULTRA FAST NSE AI SCANNER", layout="wide")
st_autorefresh(interval=5000, key="refresh")

st.title("⚡ PRO NSE AI SCANNER (ULTRA FAST)")
st.markdown("---")

# =============================
# NSE SECTORS
# =============================
sectors = {
    "Nifty 50": ["RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS"],
    "Banking": ["SBIN.NS","AXISBANK.NS","KOTAKBANK.NS","PNB.NS"],
    "IT": ["WIPRO.NS","HCLTECH.NS","TECHM.NS"],
    "Auto": ["MARUTI.NS","TATAMOTORS.NS","M&M.NS"],
    "FMCG": ["ITC.NS","HINDUNILVR.NS","NESTLEIND.NS"]
}

selected_sector = st.selectbox("📊 Sector", list(sectors.keys()))
stocks = sectors[selected_sector]

# 🔥 LIMIT CONTROL
limit = st.slider("📌 Stocks Limit", 3, 15, 5)
stocks = stocks[:limit]

# =============================
# DATA CACHE
# =============================
@st.cache_data(ttl=60)
def get_data(tickers):
    return yf.download(tickers, period="60d", interval="15m", group_by="ticker")

@st.cache_data(ttl=60)
def get_bn_data():
    return yf.download("^NSEBANK", period="5d", interval="5m")

data = get_data(stocks)
bn_df = get_bn_data()

# =============================
# FUNCTIONS
# =============================
def get_trend(df):
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    return "UP" if df['EMA20'].iloc[-1] > df['EMA50'].iloc[-1] else "DOWN"

def get_entry(df, signal):
    prev = df.iloc[-2]

    if "BUY" in signal:
        entry = prev['High']
        sl = prev['Low']
        target = entry + (entry - sl)*1.5
    else:
        entry = prev['Low']
        sl = prev['High']
        target = entry - (sl - entry)*1.5

    return round(entry,2), round(sl,2), round(target,2)

def candle(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]

    if last['Close'] > last['Open'] and last['Close'] > prev['High']:
        return "BUY"
    elif last['Close'] < last['Open'] and last['Close'] < prev['Low']:
        return "SELL"
    else:
        return "WEAK"

def bn_scalp(df):
    df['EMA5'] = df['Close'].ewm(span=5).mean()
    df['EMA13'] = df['Close'].ewm(span=13).mean()
    return "BUY" if df['EMA5'].iloc[-1] > df['EMA13'].iloc[-1] else "SELL"

@st.cache_resource
def train(X,y):
    model = RandomForestClassifier(n_estimators=50)
    model.fit(X,y)
    return model

# =============================
# ANALYZE
# =============================
results = []

for stock in stocks:
    try:
        df = data[stock].dropna()

        df['EMA20'] = df['Close'].ewm(span=20).mean()
        df['EMA50'] = df['Close'].ewm(span=50).mean()

        df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
        df.dropna(inplace=True)

        X = df[['EMA20','EMA50']]
        y = df['Target']

        if len(X) < 50:
            continue

        model = train(X,y)
        pred = model.predict(X.iloc[[-1]])[0]

        signal = "BUY" if pred==1 else "SELL"

        price = df['Close'].iloc[-1]

        entry, sl, target = get_entry(df, signal)

        # FAST MULTI TF
        t5 = get_trend(df.tail(50))
        t15 = get_trend(df)
        t1h = get_trend(df.resample("1H").last())

        cndl = candle(df)
        bn = bn_scalp(bn_df)

        results.append({
            "Stock": stock,
            "Signal": signal,
            "Price": round(price,2),
            "Entry": entry,
            "SL": sl,
            "Target": target,
            "5M": t5,
            "15M": t15,
            "1H": t1h,
            "Candle": cndl,
            "BN": bn
        })

    except:
        continue

df_res = pd.DataFrame(results)

# =============================
# UI
# =============================
st.subheader("🔥 FAST TRADING TABLE")
st.dataframe(df_res, use_container_width=True)

# MULTI BOX
if not df_res.empty:
    stock_sel = st.selectbox("Select Stock", df_res["Stock"])
    row = df_res[df_res["Stock"] == stock_sel].iloc[0]

    c1, c2, c3 = st.columns(3)
    c1.metric("5M", row["5M"])
    c2.metric("15M", row["15M"])
    c3.metric("1H", row["1H"])

# CHART
if not df_res.empty:
    st.subheader("📈 Chart")
    chart_stock = st.selectbox("Chart Stock", df_res["Stock"], key="chart")
    st.line_chart(data[chart_stock]["Close"].resample("1D").last())

# DAILY PLAN
st.subheader("💰 Daily Plan")
capital = st.number_input("Capital", value=10000)
st.write("Risk:", capital*0.02)
st.write("Target:", capital*0.03)
