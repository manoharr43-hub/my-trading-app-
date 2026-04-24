import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V6", layout="wide")
st_autorefresh(interval=60000, key="refresh")

st.title("🚀 NSE AI PRO DASHBOARD V6")
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
# SAFE DATA LOADER
# =============================
def get_data(stock):
    try:
        df = yf.Ticker(stock + ".NS").history(period="5d", interval="15m")
        if df is None or df.empty:
            return None
        return df.dropna()
    except:
        return None

# =============================
# AI SCORE
# =============================
def ai_score(df):
    if df is None:
        return 0

    close = df['Close']

    ema20 = close.ewm(span=20).mean()
    ema50 = close.ewm(span=50).mean()

    score = 0

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
    else:
        score += 10

    if df['Volume'].iloc[-1] > df['Volume'].rolling(20).mean().iloc[-1]:
        score += 40
    else:
        score += 10

    return min(score, 100)

# =============================
# SIGNAL ENGINE
# =============================
def signal(df):
    if df is None:
        return "NO DATA"

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
# LEVELS
# =============================
def levels(price):
    return price, price*0.98, price*1.03, price*1.06

# =============================
# CHART (FIXED CLARITY)
# =============================
def chart(df, stock):

    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close']
    ))

    fig.update_layout(
        title=f"{stock} CHART",
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)

# =============================
# MAIN DASHBOARD
# =============================
data = []

if st.button("🔍 RUN SCANNER"):

    for s in stocks:
        df = get_data(s)

        if df is None:
            continue
