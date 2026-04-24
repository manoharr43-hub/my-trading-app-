import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import plotly.graph_objects as go

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO DASHBOARD V2", layout="wide")
st_autorefresh(interval=60000, key="refresh")

st.title("🚀 NSE AI PRO DASHBOARD V2")
st.markdown("---")

# =============================
# STOCKS
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
# TRADE LEVELS
# =============================
def trade_levels(price):
    return price, price*0.98, price*1.03, price*1.06

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

    fig.update_layout(title=f"{stock} Chart", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

# =============================
# DASHBOARD ENGINE
# =============================
dashboard = []

if st.button("🔍 RUN AI DASHBOARD"):

    for s in stocks:
        try:
            df = yf.Ticker(s+".NS").history(period="5d", interval="15m")

            if df.empty:
                continue

            df = df.dropna()

            price = df['Close'].iloc[-1]
            score = ai_score(df)
            entry, sl, t1, t2 = trade_levels(price)

            dashboard.append({
                "Stock": s,
                "Price": round(price,2),
                "AI Score": score,
                "Entry": round(entry,2),
                "StopLoss": round(sl,2),
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
# CHART VIEW
# =============================
st.markdown("---")

if st.button("📈 SHOW CHARTS"):

    for s in stocks[:5]:
        df = yf.Ticker(s+".NS").history(period="5d", interval="15m")
        if not df.empty:
            show_chart(df, s)
