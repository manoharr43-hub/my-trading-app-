import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide")
st.title("🚀 NSE AI PRO - SAFE TEST VERSION")

stocks = ["RELIANCE", "HDFCBANK", "INFY"]

stock = st.selectbox("Select Stock", stocks)
interval = st.selectbox("Interval", ["5m", "15m", "1h"])

@st.cache_data
def load_data(symbol, interval):
    try:
        df = yf.Ticker(symbol + ".NS").history(period="5d", interval=interval)
        df = df.tz_localize(None)
        return df
    except:
        return pd.DataFrame()

df = load_data(stock, interval)

if df.empty:
    st.error("❌ Data not loading (Check internet or stock symbol)")
else:
    st.success("✅ Data Loaded Successfully")

    # Indicators
    df['EMA20'] = df['Close'].ewm(span=20).mean()

    tp = (df['High'] + df['Low'] + df['Close']) / 3
    df['VWAP'] = (tp * df['Volume']).cumsum() / df['Volume'].cumsum()

    # Chart
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close
