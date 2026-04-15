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
st.set_page_config(page_title="🔥 PRO NSE AI SCANNER ULTIMATE", layout="wide")
st_autorefresh(interval=5000, key="refresh")

st.title("🔥 PRO NSE AI SCANNER (ULTIMATE PRO VERSION)")
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
# DATA
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
# TREND
# =============================
def get_trend(df):
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    return "UP" if df['EMA20'].iloc[-1] > df['EMA50'].iloc[-1] else "DOWN"

# =============================
# ENTRY
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
# CANDLE CONFIRM
# =============================
def candle_confirmation(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]

    if last['Close'] > last['Open'] and last['Close'] > prev['High']:
        return "✅ STRONG BUY"
    elif last['Close'] < last['Open'] and last['Close'] < prev['Low']:
        return "🔻 STRONG SELL"
    else:
        return "⚖️ WEAK"

# =============================
# BANKNIFTY SCALPING
# =============================
def banknifty_scalping():
    df = yf.download("^NSEBANK", period="5d", interval="5m")

    df['EMA5'] = df['Close'].ewm(span=5).mean()
    df['EMA13'] = df['Close'].ewm(span=13).mean()

    last = df.iloc[-1]

    if last['EMA5'] > last['EMA13']:
        return "⚡ BN BUY"
    else:
        return "⚡ BN SELL"

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

    candle = candle_confirmation(df)
    bn_signal = banknifty_scalping()

    return signal, price, entry, sl, target, t5, t15, t1h, candle, bn_signal

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

        signal, price, entry, sl, target, t5, t15, t1h, candle, bn_signal = out

        results.append({
            "Stock": stock,
            "Signal": signal,
            "Price": round(price,2),
            "Entry": entry,
            "Stoploss": sl,
            "Target": target,
            "5M": t5,
            "15M": t15,
            "1H": t1h,
            "Candle": candle,
            "BankNifty": bn_signal
        })

        time.sleep(0.3)

    except:
        continue

df_res = pd.DataFrame(results)

st.subheader("🔥 TRADING TABLE")
st.dataframe(df_res, use_container_width=True)

# =============================
# MULTI TF BOX
# =============================
st.subheader("📦 Multi Timeframe")

if not df_res.empty:
    stock_sel = st.selectbox("Select Stock", df_res["Stock"])
    row = df_res[df_res["Stock"] == stock_sel].iloc[0]

    c1, c2, c3 = st.columns(3)
    c1.metric("5 MIN", row["5M"])
    c2.metric("15 MIN", row["15M"])
    c3.metric("1 HOUR", row["1H"])

# =============================
# CHART
# =============================
st.subheader("📈 Chart")

if not df_res.empty:
    chart_stock = st.selectbox("Chart Stock", df_res["Stock"], key="chart")
    chart_data = data[chart_stock]["Close"].resample("1D").last()
    st.line_chart(chart_data)

# =============================
# DAILY PLAN
# =============================
st.subheader("💰 DAILY PLAN")

capital = st.number_input("Capital", value=10000)
risk = capital * 0.02
target_daily = capital * 0.03

st.write(f"Risk per trade: ₹{risk}")
st.write(f"Daily Target: ₹{target_daily}")
st.write("Trades per day: 2-3 only")
