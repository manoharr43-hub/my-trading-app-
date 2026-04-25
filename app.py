import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V5 LIVE", layout="wide")
st_autorefresh(interval=60000, key="refresh")

st.title("🚀 NSE AI PRO V5 (LIVE ONLY + BIG PLAYER)")
st.markdown("---")

# =============================
# STOCK LIST
# =============================
sector_map = {
    "Banking": ["HDFCBANK","ICICIBANK","SBIN","AXISBANK","KOTAKBANK"],
    "IT": ["TCS","INFY","HCLTECH","WIPRO","TECHM"],
    "Pharma": ["SUNPHARMA","DRREDDY","CIPLA"],
    "Auto": ["MARUTI","M&M","TATAMOTORS"],
    "Metals": ["JSWSTEEL","TATASTEEL","HINDALCO"],
    "FMCG": ["ITC","RELIANCE","LT","BHARTIARTL"]
}

all_stocks = list(set(sum(sector_map.values(), [])))

# =============================
# TIME FORMAT (ONLY 9:30 AM)
# =============================
def clean_time(ts):
    return pd.to_datetime(ts).strftime("%I:%M %p").lstrip("0")

# =============================
# DATA LOAD
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
    rs = gain / (loss + 1e-9)
    return (100 - (100 / (1 + rs))).fillna(50)

# =============================
# AI MODEL
# =============================
def ai_predict(df):
    df = df.copy().dropna()

    if len(df) < 30:
        return None

    df['Target'] = df['Close'].shift(-1)
    df.dropna(inplace=True)

    try:
        X = df[['Close','Volume']]
        y = df['Target']

        model = LinearRegression()
        model.fit(X, y)

        return model.predict(X.iloc[-1].values.reshape(1, -1))[0]
    except:
        return None

# =============================
# BIG PLAYER DETECTION
# =============================
def big_player(df, stock):
    df = df.copy()

    df['AvgVol'] = df['Volume'].rolling(20).mean()
    df['Spike'] = df['Volume'] > (df['AvgVol'] * 2)
    df['Move'] = df['Close'].diff()

    entries = []

    for i in range(len(df)):
        if df['Spike'].iloc[i] and df['Move'].iloc[i] > 0:
            entries.append({
                "Stock": stock,
                "Type": "BIG BUY",
                "Price": df['Close'].iloc[i],
                "Time": clean_time(df.index[i])
            })

        elif df['Spike'].iloc[i] and df['Move'].iloc[i] < 0:
            entries.append({
                "Stock": stock,
                "Type": "BIG SELL",
                "Price": df['Close'].iloc[i],
                "Time": clean_time(df.index[i])
            })

    return entries

# =============================
# ANALYSIS ENGINE
# =============================
def analyze(df):
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    df['AvgVol'] = df['Volume'].rolling(20).mean()

    r = rsi(df)
    pred = ai_predict(df)

    signal = "WAIT"

    if pred:
        signal = "BUY" if pred > df['Close'].iloc[-1] else "SELL"

    vol_ok = df['Volume'].iloc[-1] > df['AvgVol'].iloc[-1]
    trend_up = df['EMA20'].iloc[-1] > df['EMA50'].iloc[-1]
    trend_down = df['EMA20'].iloc[-1] < df['EMA50'].iloc[-1]

    final = "⚠️ WAIT"

    if signal == "BUY" and r.iloc[-1] < 70 and vol_ok and trend_up:
        final = "🚀 STRONG BUY"

    elif signal == "SELL" and r.iloc[-1] > 30 and vol_ok and trend_down:
        final = "💀 STRONG SELL"

    return signal, round(r.iloc[-1],2), final

# =============================
# LIVE START
# =============================
if st.button("🔍 START LIVE V5"):

    results = []
    big_entries = []

    for s in all_stocks:
        try:
            df = load_data(s)
            df = df.between_time("09:15","15:30")

            if len(df) < 50:
                continue

            signal, rsi_v, final = analyze(df)
            big = big_player(df, s)

            results.append({
                "Stock": s,
                "Signal": signal,
                "FINAL": final,
                "RSI": rsi_v
            })

            big_entries += big

        except:
            pass

    st.session_state.live_res = results
    st.session_state.big_entries = big_entries

# =============================
# DISPLAY
# =============================
if "live_res" in st.session_state:

    st.subheader("📊 LIVE SIGNALS")
    st.dataframe(pd.DataFrame(st.session_state.live_res))

    st.subheader("🐋 BIG PLAYER ENTRIES")

    if st.session_state.big_entries:
        df_big = pd.DataFrame(st.session_state.big_entries)
        st.dataframe(df_big)
    else:
        st.info("No Big Player activity yet")

    # =============================
    # CHART
    # =============================
    stock = st.selectbox(
        "📈 Chart",
        pd.DataFrame(st.session_state.live_res)["Stock"].unique()
    )

    df_chart = load_data(stock)
    df_chart = df_chart.between_time("09:15","15:30")

    fig = go.Figure(data=[go.Candlestick(
        x=df_chart.index,
        open=df_chart['Open'],
        high=df_chart['High'],
        low=df_chart['Low'],
        close=df_chart['Close']
    )])

    # BIG PLAYER MARKERS
    df_big = pd.DataFrame(st.session_state.big_entries)

    if not df_big.empty:
        df_big = df_big[df_big["Stock"] == stock]

        for _, row in df_big.iterrows():
            color = "green" if row["Type"] == "BIG BUY" else "red"

            fig.add_trace(go.Scatter(
                x=[df_chart.index[0]],
                y=[row["Price"]],
                mode="markers+text",
                marker=dict(size=10, color=color),
                text=[row["Type"]],
                name=row["Type"]
            ))

    st.plotly_chart(fig, use_container_width=True)
