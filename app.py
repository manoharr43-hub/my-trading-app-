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
st.set_page_config(page_title="🔥 NSE AI PRO V4", layout="wide")
st_autorefresh(interval=60000, key="refresh")

st.title("🚀 NSE AI PRO V4 - SMART MONEY DASHBOARD")
st.markdown("---")

# =============================
# CACHE DATA
# =============================
@st.cache_data(ttl=300)
def load_data(stock):
    return yf.Ticker(stock + ".NS").history(period="1d", interval="5m")

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
# BIG PLAYER ENTRY
# =============================
def big_player(df):
    df = df.copy()

    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    df['AvgVol'] = df['Volume'].rolling(20).mean()

    last = df['Close'].iloc[-1]
    vol = df['Volume'].iloc[-1]
    avg_vol = df['AvgVol'].iloc[-1]

    resistance = df['High'].rolling(20).max().iloc[-2]
    support = df['Low'].rolling(20).min().iloc[-2]

    if last > resistance and vol > avg_vol * 1.5 and df['EMA20'].iloc[-1] > df['EMA50'].iloc[-1]:
        return "BUY", last

    elif last < support and vol > avg_vol * 1.5 and df['EMA20'].iloc[-1] < df['EMA50'].iloc[-1]:
        return "SELL", last

    return None, None

# =============================
# STRENGTH SCORE
# =============================
def strength_score(df):
    df = df.copy()

    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    df['AvgVol'] = df['Volume'].rolling(20).mean()

    r = rsi(df).iloc[-1]

    score = 0

    if df['EMA20'].iloc[-1] > df['EMA50'].iloc[-1]:
        score += 2
    else:
        score -= 2

    if df['Volume'].iloc[-1] > df['AvgVol'].iloc[-1]:
        score += 1

    if r < 70:
        score += 1
    else:
        score -= 1

    return score

# =============================
# ANALYSIS
# =============================
def analyze(df):
    if df is None or len(df) < 50:
        return None

    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    r = rsi(df)
    pred = ai_predict(df)

    signal = "WAIT"

    if pred:
        signal = "BUY" if pred > df['Close'].iloc[-1] else "SELL"

    vol_ok = df['Volume'].iloc[-1] > df['Volume'].rolling(20).mean().iloc[-1]

    trend_up = df['EMA20'].iloc[-1] > df['EMA50'].iloc[-1]
    trend_down = df['EMA20'].iloc[-1] < df['EMA50'].iloc[-1]

    final = "⚠️ WAIT"

    if signal == "BUY" and r.iloc[-1] < 70 and vol_ok and trend_up:
        final = "🚀 STRONG BUY"

    elif signal == "SELL" and r.iloc[-1] > 30 and vol_ok and trend_down:
        final = "💀 STRONG SELL"

    return signal, round(r.iloc[-1],2), final

# =============================
# CHART
# =============================
def plot_chart(df, stock):
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close']
    ))

    # BIG PLAYER
    sig, lvl = big_player(df)

    if sig == "BUY":
        fig.add_trace(go.Scatter(
            x=[df.index[-1]],
            y=[lvl],
            mode="markers+text",
            text=["🟢 BIG BUY"],
            marker=dict(size=14)
        ))

    elif sig == "SELL":
        fig.add_trace(go.Scatter(
            x=[df.index[-1]],
            y=[lvl],
            mode="markers+text",
            text=["🔴 BIG SELL"],
            marker=dict(size=14)
        ))

    fig.update_layout(height=600)
    st.plotly_chart(fig, use_container_width=True)

# =============================
# MAIN RUN
# =============================
if st.button("🚀 RUN V4 DASHBOARD"):

    results = []
    strength_list = []

    for s in all_stocks:
        try:
            df = load_data(s)
            df = df.between_time("09:15","15:30")

            if len(df) < 50:
                continue

            res = analyze(df)

            if res:
                signal, rsi_v, final = res

                results.append({
                    "Stock": s,
                    "Signal": signal,
                    "RSI": rsi_v,
                    "FINAL": final
                })

            score = strength_score(df)

            strength_list.append({
                "Stock": s,
                "Score": score
            })

        except:
            pass

    st.session_state.results = results
    st.session_state.strength = strength_list

# =============================
# DISPLAY
# =============================
if "results" in st.session_state:

    df_res = pd.DataFrame(st.session_state.results)

    st.subheader("📊 LIVE SIGNALS V4")
    st.dataframe(df_res, use_container_width=True)

# =============================
# STRONG / WEAK STOCKS
# =============================
if "strength" in st.session_state:

    df_strength = pd.DataFrame(st.session_state.strength)

    strong = df_strength.sort_values("Score", ascending=False).head(5)
    weak = df_strength.sort_values("Score", ascending=True).head(5)

    st.markdown("---")
    st.subheader("🟢 TOP 5 STRONG STOCKS")
    st.dataframe(strong, use_container_width=True)

    st.subheader("🔴 TOP 5 WEAK STOCKS")
    st.dataframe(weak, use_container_width=True)

    stock = st.selectbox("📈 Chart View", df_strength["Stock"])

    df_chart = load_data(stock)
    df_chart = df_chart.between_time("09:15","15:30")

    plot_chart(df_chart, stock)
