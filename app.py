import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh
import plotly.graph_objects as go

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO TERMINAL", layout="wide")
st_autorefresh(interval=60000, key="refresh")

st.title("🚀 NSE AI PRO TERMINAL")
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
# ANALYSIS ENGINE
# =============================
def analyze_data(df):
    if df is None or len(df) < 20:
        return None

    e20 = df['Close'].ewm(span=20).mean()
    e50 = df['Close'].ewm(span=50).mean()

    vol = df['Volume']
    avg_vol = vol.rolling(20).mean()

    if pd.isna(avg_vol.iloc[-1]):
        return None

    trend = "CALL STRONG" if e20.iloc[-1] > e50.iloc[-1] else "PUT STRONG"

    signal = "WAIT"
    if e20.iloc[-1] > e50.iloc[-1] and vol.iloc[-1] > avg_vol.iloc[-1]:
        signal = "🚀 STRONG BUY"
    elif e20.iloc[-1] < e50.iloc[-1] and vol.iloc[-1] > avg_vol.iloc[-1]:
        signal = "💀 STRONG SELL"

    return trend, signal

# =============================
# BREAKOUT ENGINE
# =============================
def breakout_engine(df, stock):
    results = []
    opening = df.between_time("09:15", "09:30")
    if opening.empty:
        return results

    high = opening['High'].max()
    low = opening['Low'].min()

    for i in range(1, len(df)-3):
        prev = df.iloc[i-1]
        curr = df.iloc[i]
        t = df.index[i]

        # BUY BREAKOUT
        if prev['Close'] <= high and curr['Close'] > high:
            future = df.iloc[i+1:i+4]
            up = sum(future['Close'] > curr['Close'])
            down = sum(future['Close'] <= curr['Close'])
            status = "🚀 CONFIRMED BUY" if up > down else "⚠️ FAILED BUY → SELL"
            results.append({"Time": t,"Stock": stock,"Type": status,"Level": round(high,2)})
            break

        # SELL BREAKOUT
        elif prev['Close'] >= low and curr['Close'] < low:
            future = df.iloc[i+1:i+4]
            down = sum(future['Close'] < curr['Close'])
            up = sum(future['Close'] >= curr['Close'])
            status = "💀 CONFIRMED SELL" if down > up else "⚠️ FAILED SELL → BUY"
            results.append({"Time": t,"Stock": stock,"Type": status,"Level": round(low,2)})
            break

    return results

# =============================
# CHART MODULE
# =============================
def plot_chart(df, stock):
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name="Candlestick"
    )])
    fig.add_trace(go.Scatter(x=df.index, y=df['Close'].ewm(span=20).mean(),
                             line=dict(color='blue', width=1), name="EMA20"))
    fig.add_trace(go.Scatter(x=df.index, y=df['Close'].ewm(span=50).mean(),
                             line=dict(color='red', width=1), name="EMA50"))
    st.plotly_chart(fig, use_container_width=True)

# =============================
# AUTO ALERTS
# =============================
def show_alert(stock, signal, price):
    if signal == "🚀 STRONG BUY":
