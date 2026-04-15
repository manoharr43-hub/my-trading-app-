import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import time
from sklearn.ensemble import RandomForestClassifier
from streamlit_autorefresh import st_autorefresh

# =============================
# PAGE CONFIG
# =============================
st.set_page_config(page_title="🔥 PRO NSE AI SCANNER PRO UI", layout="wide")
st_autorefresh(interval=5000, key="refresh")

st.title("🔥 PRO NSE AI SCANNER (SMART UI)")
st.markdown("---")

headers = {"User-Agent": "Mozilla/5.0"}

# =============================
# NSE SECTORS (EXPANDED)
# =============================
sectors = {
    "Nifty 50": ["RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS"],
    "Banking": ["SBIN.NS","AXISBANK.NS","KOTAKBANK.NS","PNB.NS"],
    "IT": ["WIPRO.NS","HCLTECH.NS","TECHM.NS"],
    "Auto": ["MARUTI.NS","TATAMOTORS.NS","M&M.NS"],
    "Pharma": ["SUNPHARMA.NS","CIPLA.NS","DRREDDY.NS"],
    "Energy": ["ONGC.NS","IOC.NS","BPCL.NS"],
    "FMCG": ["ITC.NS","HINDUNILVR.NS","NESTLEIND.NS"],
    "Metals": ["TATASTEEL.NS","JSWSTEEL.NS","HINDALCO.NS"],
    "Power": ["NTPC.NS","POWERGRID.NS","ADANIPOWER.NS"],
    "Infra": ["LT.NS","IRCTC.NS","NBCC.NS"],
    "Telecom": ["BHARTIARTL.NS","IDEA.NS"],
    "Finance": ["BAJFINANCE.NS","BAJAJFINSV.NS","HDFCLIFE.NS"]
}

selected_sector = st.selectbox("📊 Select Sector", list(sectors.keys()))
stocks = sectors[selected_sector]

# =============================
# DATA FETCH
# =============================
@st.cache_data(ttl=120)
def get_data(tickers):
    return yf.download(tickers, period="60d", interval="15m", group_by="ticker")

# =============================
# LIVE PRICE
# =============================
def get_live_price(symbol):
    try:
        s = requests.Session()
        s.get("https://www.nseindia.com", headers=headers)
        url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol.replace('.NS','')}"
        return s.get(url, headers=headers).json()['priceInfo']['lastPrice']
    except:
        return None

# =============================
# TREND FUNCTION
# =============================
def get_trend(df):
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    return "UP" if df['EMA20'].iloc[-1] > df['EMA50'].iloc[-1] else "DOWN"

# =============================
# ENTRY LOGIC
# =============================
def get_entry_point(df, signal):
    prev = df.iloc[-2]

    if "BUY" in signal:
        entry = round(prev['High'], 2)
        sl = round(prev['Low'], 2)
        target = round(entry + (entry - sl)*1.5, 2)
    else:
        entry = round(prev['Low'], 2)
        sl = round(prev['High'], 2)
        target = round(entry - (sl - entry)*1.5, 2)

    return entry, sl, target

# =============================
# MODEL
# =============================
@st.cache_resource
def train(X,y):
    model = RandomForestClassifier(n_estimators=80)
    model.fit(X,y)
    return model

# =============================
# ANALYZE
# =============================
def analyze(df, stock):
    df = df.copy()

    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
    df.dropna(inplace=True)

    X = df[['EMA20','EMA50']]
    y = df['Target']

    if len(X) < 50:
        return None

    model = train(X,y)
    pred = model.predict(X.iloc[[-1]])[0]

    signal = "🟢 BUY" if pred==1 else "🔴 SELL"

    price = get_live_price(stock)
    if not price:
        price = df['Close'].iloc[-1]

    entry, sl, target = get_entry_point(df, signal)

    # MULTI TF
    df5 = yf.download(stock, period="10d", interval="5m")
    df1h = yf.download(stock, period="60d", interval="1h")

    t5 = get_trend(df5)
    t15 = get_trend(df)
    t1h = get_trend(df1h)

    return signal, price, entry, sl, target, t5, t15, t1h

# =============================
# RUN
# =============================
data = get_data(stocks)

results = []

for stock in stocks:
    try:
        df = data[stock].dropna()
        out = analyze(df, stock)
        if out is None: continue

        signal, price, entry, sl, target, t5, t15, t1h = out

        results.append({
            "Stock": stock,
            "Signal": signal,
            "Price": round(price,2),
            "Entry": entry,
            "Stoploss": sl,
            "Target": target,
            "5M": t5,
            "15M": t15,
            "1H": t1h
        })

        time.sleep(0.3)

    except:
        continue

df_res = pd.DataFrame(results)

st.subheader("🔥 TRADING TABLE")
st.dataframe(df_res, use_container_width=True)

# =============================
# MULTI TF 3 BOX UI
# =============================
st.subheader("📦 Multi Timeframe View")

if not df_res.empty:
    stock_sel = st.selectbox("Select Stock", df_res["Stock"])
    row = df_res[df_res["Stock"] == stock_sel].iloc[0]

    col1, col2, col3 = st.columns(3)
    col1.metric("5 MIN", row["5M"])
    col2.metric("15 MIN", row["15M"])
    col3.metric("1 HOUR", row["1H"])

# =============================
# CHART
# =============================
st.subheader("📈 Chart")

if not df_res.empty:
    stock_chart = st.selectbox("Select Stock for Chart", df_res["Stock"], key="chart")
    chart_data = data[stock_chart]["Close"].resample("1D").last()
    st.line_chart(chart_data)
