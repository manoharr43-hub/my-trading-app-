import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="🔥 NSE AI + Option Chain App", layout="wide")

# =============================
# AUTO REFRESH
# =============================
st_autorefresh(interval=20000, key="refresh")

# =============================
# NSE SECTORS
# =============================
sectors = {
    "Nifty 50": ["RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS"],
    "Banking": ["SBIN.NS","HDFCBANK.NS","ICICIBANK.NS","AXISBANK.NS"],
    "IT": ["INFY.NS","TCS.NS","WIPRO.NS"],
    "Auto": ["TATAMOTORS.NS","MARUTI.NS","M&M.NS"]
}

# =============================
# SIDEBAR
# =============================
with st.sidebar:
    st.header("📊 Controls")
    sector = st.selectbox("Select Sector", list(sectors.keys()))
    show_option = st.checkbox("Show Option Chain", True)

# =============================
# COLOR
# =============================
def color_signal(val):
    if "BUY" in str(val):
        return "background-color: green; color: white"
    elif "SELL" in str(val):
        return "background-color: red; color: white"
    return ""

# =============================
# AI ANALYSIS
# =============================
def analyze(df):
    try:
        if df is None or len(df) < 40:
            return None

        df = df.copy()

        df['EMA20'] = df['Close'].ewm(span=20).mean()
        df['EMA50'] = df['Close'].ewm(span=50).mean()
        df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / (df['Volume'].cumsum()+1e-9)

        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain/(loss+1e-9)
        df['RSI'] = 100-(100/(1+rs))

        df['Target'] = np.where(df['Close'].shift(-1)>df['Close'],1,0)
        df.dropna(inplace=True)

        X = df[['EMA20','EMA50','RSI','VWAP']]
        y = df['Target']

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

        model = RandomForestClassifier(n_estimators=50, max_depth=5)
        model.fit(X_train, y_train)

        acc = round(model.score(X_test, y_test)*100,2)

        pred = model.predict(X.iloc[[-1]])[0]
        signal = "BUY" if pred==1 else "SELL"

        vol = df['Volume'].iloc[-1] / (df['Volume'].rolling(20).mean().iloc[-1] + 1e-9)

        return df, signal, acc, vol
    except:
        return None

# =============================
# SCANNER
# =============================
def run_scanner(stocks):
    results = []
    data = yf.download(stocks, period="5d", interval="5m", group_by='ticker', progress=False)

    for s in stocks:
        try:
            df = data[s].dropna()

            res = analyze(df)
            if res is None:
                continue

            df, ai, acc, vol = res
            last = df.iloc[-1]

            price = round(last['Close'],2)
            trend = "UP" if last['EMA20'] > last['EMA50'] else "DOWN"

            signal = "WAIT"
            if ai=="BUY" and trend=="UP":
                signal = "🔥 BUY"
            elif ai=="SELL" and trend=="DOWN":
                signal = "🔥 SELL"

            results.append({
                "Stock": s.replace(".NS",""),
                "Price": price,
                "Trend": trend,
                "AI": ai,
                "Accuracy": acc,
                "Signal": signal
            })
        except:
            continue

    return pd.DataFrame(results)

# =============================
# OPTION CHAIN
# =============================
def option_chain():
    try:
        url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
        headers = {"User-Agent": "Mozilla/5.0"}

        session = requests.Session()
        data = session.get(url, headers=headers).json()

        records = data['records']['data']

        rows = []
        for item in records:
            rows.append({
                "Strike": item['strikePrice'],
                "Call OI": item.get('CE', {}).get('openInterest', 0),
                "Put OI": item.get('PE', {}).get('openInterest', 0)
            })

        df = pd.DataFrame(rows)

        support = df.loc[df['Put OI'].idxmax()]
        resistance = df.loc[df['Call OI'].idxmax()]

        return df, support['Strike'], resistance['Strike']

    except:
        return None, None, None

# =============================
# UI
# =============================
st.title("🔥 NSE AI + OPTION CHAIN APP")

df = run_scanner(sectors[sector])

if not df.empty:
    st.subheader("📊 Scanner Results")
    st.dataframe(df.style.map(color_signal, subset=['Signal']), use_container_width=True)

    stock = st.selectbox("📈 Select Stock", df['Stock'])

    chart = yf.download(stock+".NS", period="1d", interval="5m")
    st.line_chart(chart['Close'])

# OPTION CHAIN
if show_option:
    st.subheader("📊 Option Chain (NIFTY)")
    oc_df, sup, res = option_chain()

    if oc_df is not None:
        st.dataframe(oc_df)
        st.success(f"Support: {sup}")
        st.error(f"Resistance: {res}")
    else:
        st.warning("Option Chain not loading")
