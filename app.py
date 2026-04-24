import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO TERMINAL", layout="wide")

st.title("🚀 NSE AI PRO TERMINAL (ULTIMATE VERSION)")
st.markdown("---")

# =============================
# NSE SECTORS (EXPANDED)
# =============================
sector_map = {
    "Banking": ["HDFCBANK","ICICIBANK","SBIN","AXISBANK","KOTAKBANK"],
    "IT": ["TCS","INFY","HCLTECH","WIPRO","TECHM"],
    "Pharma": ["SUNPHARMA","DRREDDY","CIPLA","LUPIN","AUROPHARMA"],
    "Auto": ["MARUTI","TATAMOTORS","M&M","EICHERMOT"],
    "FMCG": ["ITC","HINDUNILVR","NESTLEIND","BRITANNIA"],
    "Energy": ["RELIANCE","ONGC","IOC","BPCL"],
    "Metals": ["TATASTEEL","JSWSTEEL","HINDALCO"],
    "Adani": ["ADANIENT","ADANIPORTS","ADANIGREEN"],
    "All NSE (Top 50)": [
        "RELIANCE","HDFCBANK","ICICIBANK","INFY","TCS","SBIN","LT","ITC",
        "AXISBANK","KOTAKBANK","HINDUNILVR","MARUTI","BHARTIARTL",
        "ASIANPAINT","SUNPHARMA","TITAN","ULTRACEMCO","NESTLEIND",
        "BAJFINANCE","WIPRO","HCLTECH","POWERGRID"
    ]
}

selected_sector = st.sidebar.selectbox("📂 Select Sector", list(sector_map.keys()))
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
# CHART
# =============================
def plot_chart(df, stock, high=None, low=None, signal=None):
    if df.empty:
        return

    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close']
    ))

    fig.add_trace(go.Scatter(x=df.index, y=df['EMA20'], name="EMA20"))
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA50'], name="EMA50"))

    if high:
        fig.add_hline(y=high, line_dash="dash", annotation_text="HIGH")
    if low:
        fig.add_hline(y=low, line_dash="dash", annotation_text="LOW")

    if signal:
        fig.add_trace(go.Scatter(
            x=[df.index[-1]],
            y=[df['Close'].iloc[-1]],
            mode="markers+text",
            text=[signal],
            marker=dict(size=12),
            textposition="top center"
        ))

    fig.update_layout(title=stock, xaxis_rangeslider_visible=False, height=500)
    st.plotly_chart(fig, use_container_width=True)

# =============================
# LIVE SCANNER
# =============================
if st.button("🔍 START LIVE SCANNER"):
    results = []

    for s in stocks:
        try:
            df = yf.Ticker(s + ".NS").history(period="5d", interval="5m")
            df = df.between_time("09:15","15:30")

            if df.empty:
                continue

            res = strategy(df)

            opening = df.between_time("09:15","09:30")
            high = opening['High'].max() if not opening.empty else None
            low = opening['Low'].min() if not opening.empty else None

            signal = None

            if res:
                signal, high, low = res
                entry = df['Close'].iloc[-1]
                sl = low if signal == "BUY" else high

                results.append({
                    "Stock": s,
                    "Signal": signal,
                    "Entry": round(entry,2),
                    "StopLoss": round(sl,2),
                    "Time": df.index[-1].strftime("%H:%M")
                })

            plot_chart(df, s, high, low, signal)

        except:
            continue

    st.subheader("📊 LIVE SIGNALS")
    st.dataframe(pd.DataFrame(results), use_container_width=True)

# =============================
# 🔥 ALL STOCK SIGNALS
# =============================
st.markdown("---")
st.subheader("🔥 ALL NSE STOCK SIGNALS (TIME)")

if st.button("⚡ RUN FULL SCANNER"):
    all_results = []

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
                sl = low if signal == "BUY" else high

                all_results.append({
                    "Time": df.index[-1].strftime("%H:%M"),
                    "Stock": s,
                    "Signal": signal,
                    "Entry": round(entry,2),
                    "StopLoss": round(sl,2)
                })

        except:
            continue

    st.dataframe(pd.DataFrame(all_results), use_container_width=True)

# =============================
# BACKTEST
# =============================
st.markdown("---")
st.subheader("📊 BACKTEST")

bt_date = st.sidebar.date_input("Select Backtest Date", datetime.now().date() - timedelta(days=1))

if st.button("📊 RUN BACKTEST"):
    bt_results = []

    for s in stocks:
        try:
            df = yf.Ticker(s + ".NS").history(
                start=pd.to_datetime(bt_date),
                end=pd.to_datetime(bt_date) + timedelta(days=1),
                interval="5m"
            )

            df = df.between_time("09:15","15:30")

            if df.empty:
                continue

            res = strategy(df)

            opening = df.between_time("09:15","09:30")
            high = opening['High'].max() if not opening.empty else None
            low = opening['Low'].min() if not opening.empty else None

            signal = None

            if res:
                signal, high, low = res
                entry = df['Close'].iloc[-1]
                sl = low if signal == "BUY" else high

                bt_results.append({
                    "Stock": s,
                    "Signal": signal,
                    "Entry": entry,
                    "StopLoss": sl
                })

            plot_chart(df, s, high, low, signal)

        except:
            continue

    st.dataframe(pd.DataFrame(bt_results), use_container_width=True)
