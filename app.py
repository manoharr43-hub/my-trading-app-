import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V3", layout="wide")
st_autorefresh(interval=60000, key="refresh")

st.title("🚀 NSE AI PRO DASHBOARD V3")
st.markdown("---")

# =============================
# STOCK LIST
# =============================
stocks = [
    "RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","ITC","LT",
    "AXISBANK","BHARTIARTL","KOTAKBANK","MARUTI","M&M","TATAMOTORS",
    "SUNPHARMA","DRREDDY","CIPLA","HCLTECH","WIPRO","TECHM",
    "JSWSTEEL","TATASTEEL","HINDALCO"
]

# =============================
# AI SCORE ENGINE
# =============================
def ai_score(df):
    score = 0
    close = df['Close']

    ema20 = close.ewm(span=20).mean()
    ema50 = close.ewm(span=50).mean()

    if ema20.iloc[-1] > ema50.iloc[-1]:
        score += 30
    else:
        score += 10

    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    if rsi.iloc[-1] < 60:
        score += 30
    elif rsi.iloc[-1] > 70:
        score += 10

    if df['Volume'].iloc[-1] > df['Volume'].rolling(20).mean().iloc[-1]:
        score += 40
    else:
        score += 10

    return min(score, 100)

# =============================
# SIGNAL ENGINE (BUY/SELL FIXED)
# =============================
def signal_engine(df):
    close = df['Close']

    ema20 = close.ewm(span=20).mean()
    ema50 = close.ewm(span=50).mean()

    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    if ema20.iloc[-1] > ema50.iloc[-1] and rsi.iloc[-1] < 65:
        return "🚀 BUY"
    elif ema20.iloc[-1] < ema50.iloc[-1] and rsi.iloc[-1] > 35:
        return "💀 SELL"
    else:
        return "WAIT"

# =============================
# TRADE LEVELS
# =============================
def levels(price):
    return price, price*0.98, price*1.03, price*1.06

# =============================
# CHARTS
# =============================
def intraday_chart(df, stock):
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close']
    ))
    fig.update_layout(title=f"{stock} Intraday Chart", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

def daily_chart(stock):
    df = yf.Ticker(stock+".NS").history(period="6mo", interval="1d")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['Close'], mode='lines'))
    fig.update_layout(title=f"{stock} Daily Chart")
    st.plotly_chart(fig, use_container_width=True)

# =============================
# MAIN DASHBOARD
# =============================
dashboard = []

if st.button("🔍 RUN AI SCANNER"):

    for s in stocks:
        try:
            df = yf.Ticker(s+".NS").history(period="5d", interval="15m")
            if df.empty:
                continue

            price = df['Close'].iloc[-1]
            score = ai_score(df)
            signal = signal_engine(df)

            entry, sl, t1, t2 = levels(price)

            dashboard.append({
                "Stock": s,
                "Price": round(price,2),
                "AI Score": score,
                "Signal": signal,
                "Entry": round(entry,2),
                "SL": round(sl,2),
                "Target1": round(t1,2),
                "Target2": round(t2,2)
            })

        except:
            continue

    df_dash = pd.DataFrame(dashboard)

    # =============================
    # TOP 5 STOCKS
    # =============================
    top5 = df_dash.sort_values("AI Score", ascending=False).head(5)

    st.subheader("🏆 TOP 5 STRONGEST STOCKS")
    st.dataframe(top5, use_container_width=True)

    st.markdown("---")

    st.subheader("📊 FULL AI DASHBOARD")
    st.dataframe(df_dash, use_container_width=True)

# =============================
# CHART SECTION
# =============================
st.markdown("---")

if st.button("📈 SHOW CHARTS"):

    for s in stocks[:5]:
        df = yf.Ticker(s+".NS").history(period="5d", interval="15m")
        if not df.empty:
            intraday_chart(df, s)

    st.markdown("### 📊 DAILY CHARTS")
    for s in stocks[:3]:
        daily_chart(s)

# =============================
# BACKTEST (SAFE VERSION)
# =============================
st.markdown("---")

def backtest(stock):
    df = yf.Ticker(stock+".NS").history(period="60d", interval="1d")
    results = []

    for i in range(20, len(df)):
        sub = df.iloc[:i]
        signal = signal_engine(sub)

        if signal != "WAIT":
            results.append({
                "Stock": stock,
                "Time": sub.index[-1],
                "Signal": signal,
                "Price": sub['Close'].iloc[-1]
            })

    return results

if st.button("📊 RUN BACKTEST"):

    all_results = []

    for s in stocks:
        try:
            all_results += backtest(s)
        except:
            continue

    st.subheader("🔥 BACKTEST RESULTS")
    st.dataframe(pd.DataFrame(all_results), use_container_width=True)
