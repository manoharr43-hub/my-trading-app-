import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh
import plotly.graph_objects as go

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO TERMINAL", layout="wide")
st_autorefresh(interval=60000, key="refresh")

st.title("🚀 NSE AI PRO TERMINAL (STRATEGY VERSION)")
st.markdown("---")

# =============================
# SECTOR
# =============================
sector_map = {
    "Banking": ["HDFCBANK","ICICIBANK","SBIN","AXISBANK","KOTAKBANK"],
    "IT": ["TCS","INFY","HCLTECH","WIPRO","TECHM"],
    "Pharma": ["SUNPHARMA","DRREDDY","CIPLA"],
}

selected_sector = st.sidebar.selectbox("Select Sector", list(sector_map.keys()))
stocks = sector_map[selected_sector]

# =============================
# INDICATORS
# =============================
def rsi(df):
    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    rs = gain.rolling(14).mean() / loss.rolling(14).mean()
    return 100 - (100/(1+rs))

def macd(df):
    e12 = df['Close'].ewm(span=12).mean()
    e26 = df['Close'].ewm(span=26).mean()
    macd = e12 - e26
    signal = macd.ewm(span=9).mean()
    return macd, signal

# =============================
# STRATEGY
# =============================
def strategy(df):
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    macd_val, sig = macd(df)
    r = rsi(df)

    opening = df.between_time("09:15","09:30")
    if opening.empty:
        return None

    high = opening['High'].max()
    low = opening['Low'].min()

    last = df.iloc[-1]
    prev = df.iloc[-2]

    # BUY
    if (
        last['Close'] > high and prev['Close'] <= high and
        df['EMA20'].iloc[-1] > df['EMA50'].iloc[-1] and
        macd_val.iloc[-1] > sig.iloc[-1] and
        40 < r.iloc[-1] < 65
    ):
        return "BUY", high, low

    # SELL
    elif (
        last['Close'] < low and prev['Close'] >= low and
        df['EMA20'].iloc[-1] < df['EMA50'].iloc[-1] and
        macd_val.iloc[-1] < sig.iloc[-1] and
        35 < r.iloc[-1] < 60
    ):
        return "SELL", high, low

    return None

# =============================
# CHART WITH BREAKOUT
# =============================
def plot_chart(df, stock, high, low, signal):
    fig = go.Figure()

    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close']
    ))

    fig.add_trace(go.Scatter(x=df.index, y=df['EMA20'], name="EMA20"))
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA50'], name="EMA50"))

    # breakout lines
    fig.add_hline(y=high, line_dash="dash", annotation_text="HIGH")
    fig.add_hline(y=low, line_dash="dash", annotation_text="LOW")

    # highlight breakout
    if signal:
        fig.add_trace(go.Scatter(
            x=[df.index[-1]],
            y=[df['Close'].iloc[-1]],
            mode="markers+text",
            text=[signal],
            marker=dict(size=12),
            textposition="top center"
        ))

    fig.update_layout(title=stock, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

# =============================
# LIVE SCANNER
# =============================
if st.button("START LIVE SCANNER"):
    results = []

    for s in stocks:
        try:
            df = yf.Ticker(s + ".NS").history(period="1d", interval="5m")
            df = df.between_time("09:15","15:30")

            if df.empty:
                continue

            res = strategy(df)

            if res:
                signal, high, low = res

                entry = df['Close'].iloc[-1]

                if signal == "BUY":
                    sl = low
                else:
                    sl = high

                results.append({
                    "Stock": s,
                    "Signal": signal,
                    "Entry": entry,
                    "StopLoss": sl
                })

                plot_chart(df, s, high, low, signal)

        except Exception as e:
            st.error(f"{s}: {e}")

    st.subheader("Signals")
    st.dataframe(pd.DataFrame(results))
