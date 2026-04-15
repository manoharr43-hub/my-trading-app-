import streamlit as st
import yfinance as yf
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 PRO NSE AI SCANNER", layout="wide")
st_autorefresh(interval=5000, key="refresh")

st.title("🔥 PRO NSE AI SCANNER (ZERO ERROR VERSION)")
st.markdown("---")

# =============================
# NSE SECTORS
# =============================
sectors = {
    "Nifty 50": ["RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS"],
    "Banking": ["SBIN.NS","AXISBANK.NS","KOTAKBANK.NS","PNB.NS"],
    "IT": ["WIPRO.NS","HCLTECH.NS","TECHM.NS"],
    "Auto": ["MARUTI.NS","TATAMOTORS.NS","M&M.NS"]
}

sector = st.selectbox("📊 Select Sector", list(sectors.keys()))
stocks = sectors[sector]

# LIMIT
limit = st.slider("📌 Stocks Limit", 3, 10, 5)
stocks = stocks[:limit]

# =============================
# SAFE DATA FETCH
# =============================
@st.cache_data(ttl=60)
def get_data_safe(tickers):
    data = {}
    for t in tickers:
        try:
            df = yf.download(t, period="60d", interval="15m")
            if not df.empty:
                df.index = pd.to_datetime(df.index)
                data[t] = df
        except:
            continue
    return data

data = get_data_safe(stocks)

# =============================
# FUNCTIONS
# =============================
def get_trend(df):
    df = df.copy()
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    return "UP" if df['EMA20'].iloc[-1] > df['EMA50'].iloc[-1] else "DOWN"

def get_entry(df, signal):
    if len(df) < 2:
        return None, None, None

    prev = df.iloc[-2]

    if signal == "BUY":
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

        if len(df) < 30:
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

        # MULTI TIMEFRAME SAFE
        t5 = get_trend(df.tail(50))
        t15 = get_trend(df)

        try:
            df_1h = df.resample("1h").last().dropna()
            t1h = get_trend(df_1h) if len(df_1h) > 10 else "N/A"
        except:
            t1h = "N/A"

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
# UI OUTPUT
# =============================
if df_res.empty:
    st.warning("⚠️ No Data Loaded (Try changing sector or limit)")
else:
    st.subheader("🔥 TRADING TABLE")
    st.dataframe(df_res, use_container_width=True)

    # MULTI TF BOX
    st.subheader("📦 Multi Timeframe View")
    stock_sel = st.selectbox("Select Stock", df_res["Stock"])
    row = df_res[df_res["Stock"] == stock_sel].iloc[0]

    c1, c2, c3 = st.columns(3)
    c1.metric("5M Trend", row["5M"])
    c2.metric("15M Trend", row["15M"])
    c3.metric("1H Trend", row["1H"])

    # CHART
    st.subheader("📈 Price Chart")
    chart_stock = st.selectbox("Chart Stock", df_res["Stock"], key="chart")
    st.line_chart(data[chart_stock]["Close"].resample("1D").last())

# =============================
# DAILY PLAN
# =============================
st.subheader("💰 Daily Plan")
capital = st.number_input("Capital", value=10000)
st.write("Risk per trade:", round(capital*0.02,2))
st.write("Daily target:", round(capital*0.03,2))
