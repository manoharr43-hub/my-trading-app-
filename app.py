import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from streamlit_autorefresh import st_autorefresh

# =============================
# PAGE CONFIG
# =============================
st.set_page_config(page_title="🔥 PRO NSE AI SCANNER", layout="wide")
st_autorefresh(interval=5000, key="refresh")

st.title("🔥 PRO NSE AI SCANNER (SuperTrend + AI)")

# =============================
# STOCK LIST
# =============================
sectors = {
    "Nifty 50": ["RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS"],
    "Banking": ["SBIN.NS","AXISBANK.NS","KOTAKBANK.NS","PNB.NS"],
    "IT": ["INFY.NS","TCS.NS","WIPRO.NS","HCLTECH.NS"],
    "Auto": ["MARUTI.NS","M&M.NS","BAJAJ-AUTO.NS"],
    "Pharma": ["SUNPHARMA.NS","DRREDDY.NS","CIPLA.NS"],
    "Energy": ["RELIANCE.NS","ONGC.NS","IOC.NS"],
}

all_stocks = list(set([s for sec in sectors.values() for s in sec]))

# =============================
# DATA
# =============================
@st.cache_data(ttl=60)
def get_data(tickers):
    return yf.download(tickers, period="20d", interval="5m", group_by='ticker', progress=False)

# =============================
# MODEL
# =============================
@st.cache_resource
def train_model(X, y):
    model = RandomForestClassifier(n_estimators=80, max_depth=6, random_state=42)
    model.fit(X, y)
    return model

# =============================
# SUPER TREND 🔥
# =============================
def supertrend(df, period=10, multiplier=3):
    df = df.copy()

    hl2 = (df['High'] + df['Low']) / 2

    df['TR'] = np.maximum(df['High'] - df['Low'],
                 np.maximum(abs(df['High'] - df['Close'].shift()),
                            abs(df['Low'] - df['Close'].shift())))

    df['ATR'] = df['TR'].rolling(period).mean()

    df['UpperBand'] = hl2 + (multiplier * df['ATR'])
    df['LowerBand'] = hl2 - (multiplier * df['ATR'])

    df['SuperTrend'] = 0.0

    for i in range(1, len(df)):
        if df['Close'].iloc[i] > df['UpperBand'].iloc[i-1]:
            df.loc[df.index[i], 'SuperTrend'] = df['LowerBand'].iloc[i]
        elif df['Close'].iloc[i] < df['LowerBand'].iloc[i-1]:
            df.loc[df.index[i], 'SuperTrend'] = df['UpperBand'].iloc[i]
        else:
            df.loc[df.index[i], 'SuperTrend'] = df['SuperTrend'].iloc[i-1]

    return df

# =============================
# ANALYSIS
# =============================
def analyze(df):
    if df is None or len(df) < 50:
        return None

    df = df.copy()

    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()

    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))

    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-9)

    # 🔥 SUPER TREND ADD
    df = supertrend(df)

    df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
    df.dropna(inplace=True)

    features = ['EMA20','EMA50','RSI','VWAP']
    X = df[features]
    y = df['Target']

    if len(X) < 30:
        return None

    X_train, _, y_train, _ = train_test_split(X, y, test_size=0.2, shuffle=False)
    model = train_model(X_train, y_train)

    pred = model.predict(X.iloc[[-1]])[0]

    price = df['Close'].iloc[-1]
    st_value = df['SuperTrend'].iloc[-1]

    # 🔥 FINAL SIGNAL (AI + SUPER TREND)
    if pred == 1 and price > st_value:
        signal = "BUY"
    elif pred == 0 and price < st_value:
        signal = "SELL"
    else:
        signal = "SIDEWAYS"

    # Volume
    avg_vol = df['Volume'].rolling(20).mean().iloc[-1]
    vol_ratio = df['Volume'].iloc[-1] / avg_vol if avg_vol > 0 else 1

    if vol_ratio > 2:
        big = "Big Buyer"
    elif vol_ratio < 0.5:
        big = "Big Seller"
    else:
        big = ""

    return df, signal, big

# =============================
# LEVELS
# =============================
def levels(df):
    support = round(df['Low'].tail(50).min(),2)
    resistance = round(df['High'].tail(50).max(),2)
    return support, resistance

# =============================
# TRADE
# =============================
def trade(price, support, resistance, signal):
    sl = round(price * 0.98,2)

    if signal == "BUY":
        t1 = round(price + (resistance - support) * 0.5,2)
        t2 = resistance
    elif signal == "SELL":
        t1 = round(price - (resistance - support) * 0.5,2)
        t2 = support
    else:
        t1, t2 = "-", "-"

    return sl, t1, t2

# =============================
# STYLE
# =============================
def highlight(row):
    if row["Signal"] == "BUY":
        return ['background-color: #2196F3; color: white'] * len(row)
    elif row["Signal"] == "SELL":
        return ['background-color: #f44336; color: white'] * len(row)
    else:
        return [''] * len(row)

# =============================
# SCANNER
# =============================
def scanner():
    results = []
    data = get_data(all_stocks)

    for s in all_stocks:
        try:
            df = data[s].dropna()
            out = analyze(df)
            if out is None:
                continue

            df, signal, big = out

            price = round(df['Close'].iloc[-1],2)
            support, resistance = levels(df)
            sl, t1, t2 = trade(price, support, resistance, signal)

            trend = "UP" if price > df['EMA50'].iloc[-1] else "DOWN"

            score = 0
            if signal == "BUY":
                score += 2
                if trend == "UP":
                    score += 1
                if big == "Big Buyer":
                    score += 2
            elif signal == "SELL":
                score += 2
                if trend == "DOWN":
                    score += 1
                if big == "Big Seller":
                    score += 2

            results.append({
                "Stock": s,
                "Price": price,
                "Signal": signal,
                "Trend": trend,
                "Support": support,
                "Resistance": resistance,
                "SL": sl,
                "T1": t1,
                "T2": t2,
                "Volume": big,
                "Score": score
            })

        except:
            continue

    return pd.DataFrame(results).sort_values(by="Score", ascending=False)

# =============================
# UI
# =============================
df = scanner()

tabs = st.tabs(list(sectors.keys()))

for i, sector in enumerate(sectors.keys()):
    with tabs[i]:
        st.dataframe(df[df["Stock"].isin(sectors[sector])]
                     .style.apply(highlight, axis=1),
                     use_container_width=True)

# =============================
# TOP TRADES
# =============================
st.subheader("🔥 TOP TRADES")
top = df[df["Score"] >= 3]
st.dataframe(top.style.apply(highlight, axis=1), use_container_width=True)

# =============================
# CHART (SUPER TREND) 🔥
# =============================
st.subheader("📈 SuperTrend Chart")

if not df.empty:
    stock = st.selectbox("Select Stock", df["Stock"])

    data = get_data([stock])
    if data is not None:
        chart_df = data[stock].dropna()
        chart_df = supertrend(chart_df)

        st.line_chart(chart_df[['Close', 'SuperTrend']])
