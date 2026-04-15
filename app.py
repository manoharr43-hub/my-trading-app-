import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI SCANNER STABLE", layout="wide")
st_autorefresh(interval=5000, key="refresh")

st.title("🔥 NSE AI SCANNER (STABLE VERSION)")
st.markdown("---")

# =============================
# SECTORS
# =============================
sectors = {
    "Nifty 50": ["RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS"],
    "Banking": ["SBIN.NS","AXISBANK.NS","KOTAKBANK.NS","PNB.NS"],
    "IT": ["WIPRO.NS","HCLTECH.NS","TECHM.NS"],
    "Auto": ["MARUTI.NS","TATAMOTORS.NS","M&M.NS"]
}

selected_sector = st.selectbox("📊 Select Sector", list(sectors.keys()))
stocks = sectors[selected_sector]

# LIMIT CONTROL
limit = st.slider("📌 Stocks Limit", 3, 10, 5)
stocks = stocks[:limit]

# =============================
# SAFE DATA FETCH
# =============================
@st.cache_data(ttl=60)
def get_data_safe(tickers):
    data_dict = {}
    for t in tickers:
        try:
            df = yf.download(t, period="60d", interval="15m")
            if df is not None and not df.empty:
                data_dict[t] = df
        except:
            continue
    return data_dict

data = get_data_safe(stocks)

# DEBUG
st.write("Loaded Stocks:", list(data.keys()))

# =============================
# FUNCTIONS
# =============================
def get_trend(df):
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    return "UP" if df['EMA20'].iloc[-1] > df['EMA50'].iloc[-1] else "DOWN"

def get_entry(df, signal):
    if len(df) < 2:
        return None, None, None

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

@st.cache_resource
def train(X,y):
    model = RandomForestClassifier(n_estimators=50)
    model.fit(X,y)
    return model

# =============================
# ANALYSIS
# =============================
results = []

for stock in stocks:
    try:
        if stock not in data:
            continue

        df = data[stock].copy()

        if df.empty or len(df) < 30:
            continue

        df['EMA20'] = df['Close'].ewm(span=20).mean()
        df['EMA50'] = df['Close'].ewm(span=50).mean()

        df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
        df.dropna(inplace=True)

        if len(df) < 30:
            continue

        X = df[['EMA20','EMA50']]
        y = df['Target']

        model = train(X,y)
        pred = model.predict(X.iloc[[-1]])[0]

        signal = "BUY" if pred==1 else "SELL"
        price = df['Close'].iloc[-1]

        entry, sl, target = get_entry(df, signal)

        if entry is None:
            continue

        # FAST MULTI TF
        t5 = get_trend(df.tail(50))
        t15 = get_trend(df)
        t1h = get_trend(df.resample("1H").last())

        results.append({
            "Stock": stock,
            "Signal": signal,
            "Price": round(price,2),
            "Entry": entry,
            "SL": sl,
            "Target": target,
            "5M": t5,
            "15M": t15,
            "1H": t1h
        })

    except Exception as e:
        st.write(f"Error in {stock}:", e)

df_res = pd.DataFrame(results)

# =============================
# OUTPUT
# =============================
if df_res.empty:
    st.error("❌ No Stocks Data Available (Check Internet / API)")
else:
    st.subheader("🔥 TRADING TABLE")
    st.dataframe(df_res, use_container_width=True)

    # MULTI TF
    stock_sel = st.selectbox("Select Stock", df_res["Stock"])
    row = df_res[df_res["Stock"] == stock_sel].iloc[0]

    c1, c2, c3 = st.columns(3)
    c1.metric("5M", row["5M"])
    c2.metric("15M", row["15M"])
    c3.metric("1H", row["1H"])

    # CHART
    st.subheader("📈 Chart")
    st.line_chart(data[stock_sel]["Close"].resample("1D").last())
