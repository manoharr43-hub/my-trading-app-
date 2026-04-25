import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V6", layout="wide")
st_autorefresh(interval=60000, key="refresh")

st.title("🚀 NSE AI PRO V6 - LIVE + SMART MONEY + BACKTEST")
st.markdown("---")

# =============================
# SESSION
# =============================
if "bt_history" not in st.session_state:
    st.session_state.bt_history = []

# =============================
# SECTORS
# =============================
sector_map = {
    "Banking": ["HDFCBANK","ICICIBANK","SBIN","AXISBANK","KOTAKBANK"],
    "IT": ["TCS","INFY","HCLTECH","WIPRO","TECHM"],
    "Auto": ["MARUTI","M&M","TATAMOTORS"],
    "FMCG": ["ITC","RELIANCE","LT","BHARTIARTL"]
}

all_stocks = list(set(sum(sector_map.values(), [])))

# =============================
# DATA
# =============================
@st.cache_data(ttl=300)
def load_data(stock):
    return yf.Ticker(stock + ".NS").history(period="1d", interval="5m")

# =============================
# RSI
# =============================
def rsi(df, period=14):
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# =============================
# AI
# =============================
def ai_predict(df):
    df = df.copy().dropna()
    if len(df) < 30:
        return None

    df['Target'] = df['Close'].shift(-1)
    df.dropna(inplace=True)

    X = df[['Close','Volume']]
    y = df['Target']

    model = LinearRegression()
    model.fit(X, y)

    return model.predict(X.iloc[-1].values.reshape(1, -1))[0]

# =============================
# BIG PLAYER
# =============================
def big_player(df):
    last = df['Close'].iloc[-1]
    res = df['High'].rolling(20).max().iloc[-2]
    sup = df['Low'].rolling(20).min().iloc[-2]

    if last > res:
        return "BUY", last
    elif last < sup:
        return "SELL", last
    return None, None

# =============================
# STRENGTH
# =============================
def strength(df):
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    score = 0

    if df['EMA20'].iloc[-1] > df['EMA50'].iloc[-1]:
        score += 2
    else:
        score -= 2

    if df['Volume'].iloc[-1] > df['Volume'].rolling(20).mean().iloc[-1]:
        score += 1

    if rsi(df).iloc[-1] < 70:
        score += 1

    return score

# =============================
# ANALYSIS
# =============================
def analyze(df):

    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    pred = ai_predict(df)

    signal = "WAIT"
    if pred:
        signal = "BUY" if pred > df['Close'].iloc[-1] else "SELL"

    r = rsi(df).iloc[-1]

    vol_ok = df['Volume'].iloc[-1] > df['Volume'].rolling(20).mean().iloc[-1]
    up = df['EMA20'].iloc[-1] > df['EMA50'].iloc[-1]
    down = df['EMA20'].iloc[-1] < df['EMA50'].iloc[-1]

    final = "WAIT"

    if signal == "BUY" and r < 70 and vol_ok and up:
        final = "STRONG BUY"
    elif signal == "SELL" and r > 30 and vol_ok and down:
        final = "STRONG SELL"

    return signal, round(r,2), final

# =============================
# ENTRY + SL + TARGET
# =============================
def entry_system(df):
    price = df['Close'].iloc[-1]
    atr = (df['High'] - df['Low']).rolling(14).mean().iloc[-1]

    sl = price - (atr * 1.5)
    tgt = price + (atr * 3)

    return round(sl,2), round(tgt,2)

# =============================
# CHART
# =============================
def show_chart(df, stock):

    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close']
    ))

    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['Close'].ewm(span=20).mean(),
        name="EMA20"
    ))

    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['Close'].ewm(span=50).mean(),
        name="EMA50"
    ))

    fig.update_layout(title=stock, height=500)

    st.plotly_chart(fig, use_container_width=True)

# =============================
# LIVE SCANNER (SECTOR)
# =============================
st.subheader("📡 LIVE SECTOR SCANNER")

for sector, stocks in sector_map.items():

    st.markdown(f"### 🔹 {sector}")

    data = []

    for stock in stocks:

        df = load_data(stock)

        if df is None or len(df) < 50:
            continue

        signal, rsi_val, final = analyze(df)
        bp, _ = big_player(df)
        score = strength(df)
        sl, tgt = entry_system(df)

        data.append({
            "Stock": stock,
            "Signal": signal,
            "RSI": rsi_val,
            "Strength": score,
            "SL": sl,
            "TARGET": tgt,
            "Big": bp if bp else "NONE"
        })

    st.dataframe(pd.DataFrame(data))

# =============================
# STRONG STOCK LIST
# =============================
st.subheader("🔥 STRONG BUY / SELL")

buy = []
sell = []

for stock in all_stocks:

    df = load_data(stock)

    if df is None or len(df) < 50:
        continue

    _, _, final = analyze(df)

    if final == "STRONG BUY":
        buy.append(stock)
    elif final == "STRONG SELL":
        sell.append(stock)

col1, col2 = st.columns(2)

with col1:
    st.success("🚀 BUY")
    st.write(buy)

with col2:
    st.error("💀 SELL")
    st.write(sell)

# =============================
# CHART VIEW
# =============================
st.subheader("📊 CHART")

selected = st.selectbox("Select Stock", all_stocks)

df = load_data(selected)

if df is not None:
    show_chart(df, selected)

# =============================
# BACKTEST DATE
# =============================
st.markdown("---")

bt_date = st.date_input("📅 Backtest Date", datetime.now().date() - timedelta(days=1))

if st.button("📊 RUN BACKTEST"):

    results = []
    progress = st.progress(0)

    for i, stock in enumerate(all_stocks):

        df = load_data(stock)

        if df is None or len(df) < 50:
            continue

        signal, rsi_val, final = analyze(df)
        bp, _ = big_player(df)
        score = strength(df)

        sl, tgt = entry_system(df)

        results.append({
            "Stock": stock,
            "Signal": signal,
            "RSI": rsi_val,
            "Final": final,
            "SL": sl,
            "TARGET": tgt,
            "Big": bp if bp else "NONE"
        })

        progress.progress((i+1)/len(all_stocks))

    df_res = pd.DataFrame(results)
    st.session_state.bt_history.append(df_res)

    st.success("✅ Backtest Done")

    st.dataframe(df_res)

    st.subheader("📊 Backtest Chart (First Stock)")
    if len(df_res) > 0:
        show_chart(load_data(df_res.iloc[0]['Stock']), df_res.iloc[0]['Stock'])

# =============================
# BACKTEST HISTORY
# =============================
st.subheader("📁 BACKTEST FOLDER")

if st.session_state.bt_history:

    for i, df in enumerate(st.session_state.bt_history[::-1]):

        with st.expander(f"Run #{i+1}"):

            st.dataframe(df)

else:
    st.info("No backtest yet")
