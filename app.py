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
st.set_page_config(page_title="🔥 NSE AI PRO V5", layout="wide")
st_autorefresh(interval=60000, key="refresh")

st.title("🚀 NSE AI PRO V5 - SMART MONEY + LIVE SCANNER + BACKTEST")
st.markdown("---")

# =============================
# SESSION STATE
# =============================
if "bt_history" not in st.session_state:
    st.session_state.bt_history = []

# =============================
# STOCK LIST
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
# AI PREDICT
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
    df = df.copy()

    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    df['AvgVol'] = df['Volume'].rolling(20).mean()

    last = df['Close'].iloc[-1]

    resistance = df['High'].rolling(20).max().iloc[-2]
    support = df['Low'].rolling(20).min().iloc[-2]

    if last > resistance:
        return "BUY", last
    elif last < support:
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
# CHART FIX (IMPORTANT)
# =============================
def show_chart(df, stock):

    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name="Price"
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

    fig.update_layout(
        title=f"{stock} Chart",
        height=500
    )

    st.plotly_chart(fig, use_container_width=True)

# =============================
# LIVE SCANNER (FIXED)
# =============================
st.subheader("📡 LIVE SCANNER")

live_data = []

for stock in all_stocks:
    df = load_data(stock)

    if df is None or len(df) < 50:
        continue

    signal, rsi_val, final = analyze(df)
    bp_signal, bp_price = big_player(df)
    score = strength(df)

    live_data.append({
        "Stock": stock,
        "Signal": signal,
        "RSI": rsi_val,
        "Final": final,
        "Big Player": bp_signal if bp_signal else "NONE",
        "Strength": score,
        "Price": round(df['Close'].iloc[-1], 2)
    })

st.dataframe(pd.DataFrame(live_data))

# =============================
# CHART SELECTOR
# =============================
st.subheader("📊 CHART VIEW")

selected_stock = st.selectbox("Select Stock", all_stocks)

df_chart = load_data(selected_stock)

if df_chart is not None:
    show_chart(df_chart, selected_stock)

# =============================
# BACKTEST
# =============================
st.markdown("---")

if st.button("📊 RUN BACKTEST"):

    results = []
    progress = st.progress(0)
    total = len(all_stocks)

    for i, stock in enumerate(all_stocks):

        df = load_data(stock)
        if df is None or len(df) < 50:
            continue

        signal, rsi_val, final = analyze(df)
        bp_signal, bp_price = big_player(df)
        score = strength(df)

        results.append({
            "Stock": stock,
            "Signal": signal,
            "RSI": rsi_val,
            "Final": final,
            "Big Player": bp_signal if bp_signal else "NONE",
            "Strength": score,
            "Price": round(df['Close'].iloc[-1], 2)
        })

        progress.progress((i+1)/total)

    st.session_state.bt_history.append(pd.DataFrame(results))

    st.success("✅ Backtest Completed")

# =============================
# BACKTEST FOLDER
# =============================
st.subheader("📁 BACKTEST FOLDER")

if st.session_state.bt_history:

    for i, df in enumerate(st.session_state.bt_history[::-1]):

        with st.expander(f"Run #{len(st.session_state.bt_history)-i}"):

            st.dataframe(df)

            st.download_button(
                "⬇️ Download CSV",
                df.to_csv(index=False),
                file_name=f"backtest_{i}.csv",
                mime="text/csv"
            )
else:
    st.info("No backtest yet")
