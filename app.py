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
st.set_page_config(page_title="🔥 NSE AI SCANNER UPGRADED", layout="wide")
st_autorefresh(interval=5000, key="refresh")

st.title("🔥 NSE AI SCANNER (UPGRADED VERSION)")
st.markdown("---")

headers = {"User-Agent": "Mozilla/5.0"}

# =============================
# NSE SECTORS
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
# INDICATORS
# =============================
def add_indicators(df):
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    df['RSI'] = 100 - (100/(1+df['Close'].pct_change().rolling(14).mean()))
    df['MACD'] = df['Close'].ewm(span=12).mean() - df['Close'].ewm(span=26).mean()
    df['SignalLine'] = df['MACD'].ewm(span=9).mean()
    return df

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
    model = RandomForestClassifier(n_estimators=100)
    model.fit(X,y)
    return model

# =============================
# ANALYZE
# =============================
def analyze(df, stock):
    df = add_indicators(df)
    df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
    df.dropna(inplace=True)

    X = df[['EMA20','EMA50','RSI','MACD','SignalLine']]
    y = df['Target']

    if len(X) < 50:
        return None

    model = train(X,y)
    pred = model.predict(X.iloc[[-1]])[0]

    signal = "🟢 BUY" if pred==1 else "🔴 SELL"
    price = get_live_price(stock) or df['Close'].iloc[-1]
    entry, sl, target = get_entry_point(df, signal)

    return signal, price, entry, sl, target, round(df['RSI'].iloc[-1],2), round(df['MACD'].iloc[-1],2)

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
        signal, price, entry, sl, target, rsi, macd = out
        results.append({
            "Stock": stock,
            "Signal": signal,
            "Price": round(price,2),
            "Entry": entry,
            "Stoploss": sl,
            "Target": target,
            "RSI": rsi,
            "MACD": macd
        })
        time.sleep(0.3)
    except:
        continue

df_res = pd.DataFrame(results)

st.subheader("🔥 TRADING TABLE")
st.dataframe(df_res, use_container_width=True)

# =============================
# CHART
# =============================
st.subheader("📈 Chart")
if not df_res.empty:
    stock_chart = st.selectbox("Select Stock for Chart", df_res["Stock"], key="chart")
    chart_data = data[stock_chart]["Close"].resample("1D").last()
    st.line_chart(chart_data)
