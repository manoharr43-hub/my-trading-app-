import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
import os

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V21", layout="wide")
st.title("🚀 NSE AI PRO V21 (SL + TP SYSTEM)")
st_autorefresh(interval=60000, key="refresh")

# =============================
# STOCKS
# =============================
stocks = [
    "HDFCBANK","ICICIBANK","SBIN","AXISBANK","KOTAKBANK","INFY","TCS","ITC","RELIANCE","LT"
]

# =============================
# DATA
# =============================
@st.cache_data(ttl=60)
def load_data(stock, interval="5m"):
    df = yf.Ticker(stock + ".NS").history(period="1d", interval=interval)
    return df.between_time("09:15","15:30") if not df.empty else pd.DataFrame()

# =============================
# 15m TREND
# =============================
@st.cache_data(ttl=60)
def get_15m_trend(stock):
    df = load_data(stock, "15m")
    if df.empty or len(df) < 20:
        return "UNKNOWN"

    ema = df['Close'].ewm(span=20).mean()
    return "UP" if df['Close'].iloc[-1] > ema.iloc[-1] else "DOWN"

# =============================
# SUPPORT / RESISTANCE
# =============================
def get_sr(df):
    if df.empty:
        return None, None
    recent = df.tail(50)
    return round(recent['Low'].min(),2), round(recent['High'].max(),2)

# =============================
# SL / TP LOGIC
# =============================
def calc_sl_tp(df, price, signal_type):
    recent_low = df['Low'].tail(20).min()
    recent_high = df['High'].tail(20).max()

    if signal_type == "BIG BUY":
        sl = recent_low
        risk = price - sl
        tp = price + (risk * 1.5)
    else:
        sl = recent_high
        risk = sl - price
        tp = price - (risk * 1.5)

    return round(sl,2), round(tp,2)

# =============================
# BIG PLAYER
# =============================
def big_player(df, stock):
    if df.empty or len(df) < 30:
        return []

    df = df.copy()
    df['EMA20'] = df['Close'].ewm(span=20).mean()

    tp = (df['High']+df['Low']+df['Close'])/3
    df['VWAP'] = (tp*df['Volume']).cumsum()/(df['Volume'].cumsum()+1)

    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    rs = gain.rolling(14).mean()/(loss.rolling(14).mean()+1e-9)
    df['RSI'] = 100-(100/(1+rs))

    df['AvgVol'] = df['Volume'].rolling(20).mean()

    signals = []

    for i in range(25,len(df)):
        price = df['Close'].iloc[i]

        vol = df['Volume'].iloc[i] > df['AvgVol'].iloc[i]*1.5
        buy = price>df['EMA20'].iloc[i] and price>df['VWAP'].iloc[i] and df['RSI'].iloc[i]>52
        sell = price<df['EMA20'].iloc[i] and price<df['VWAP'].iloc[i] and df['RSI'].iloc[i]<48

        if vol and buy:
            signals.append({"Stock":stock,"Type":"BIG BUY","Price":price,"TimeRaw":df.index[i]})

        elif vol and sell:
            signals.append({"Stock":stock,"Type":"BIG SELL","Price":price,"TimeRaw":df.index[i]})

    return signals[-10:]

# =============================
# LIVE
# =============================
if st.button("🔍 START LIVE"):

    final = []

    for s in stocks:

        df5 = load_data(s,"5m")
        if df5.empty:
            continue

        trend = get_15m_trend(s)
        support,resistance = get_sr(df5)

        signals = big_player(df5,s)

        for sig in signals:

            price = sig["Price"]

            # FILTER BY TREND
            if not (
                (trend=="UP" and sig["Type"]=="BIG BUY") or
                (trend=="DOWN" and sig["Type"]=="BIG SELL")
            ):
                continue

            sl,tp = calc_sl_tp(df5,price,sig["Type"])

            sig["Entry"] = price
            sig["Stoploss"] = sl
            sig["Target"] = tp
            sig["Support"] = support
            sig["Resistance"] = resistance
            sig["Trend"] = trend

            final.append(sig)

    st.session_state.live_big = final

# =============================
# DISPLAY
# =============================
if st.session_state.live_big:

    df = pd.DataFrame(st.session_state.live_big)

    st.subheader("🐋 BIG PLAYER WITH SL/TP")
    st.dataframe(df, use_container_width=True)

    stock = st.selectbox("📈 Chart", stocks)
    dfc = load_data(stock,"5m")

    if not dfc.empty:

        fig = go.Figure(data=[go.Candlestick(
            x=dfc.index,
            open=dfc['Open'],
            high=dfc['High'],
            low=dfc['Low'],
            close=dfc['Close']
        )])

        df_sig = df[df["Stock"]==stock]

        for _,r in df_sig.iterrows():
            fig.add_trace(go.Scatter(
                x=[r["TimeRaw"]],
                y=[r["Entry"]],
                mode="markers+text",
                text=[f"{r['Type']} SL:{r['Stoploss']} TP:{r['Target']}"],
                marker=dict(size=10,color="green" if r["Type"]=="BIG BUY" else "red")
            ))

        st.plotly_chart(fig,use_container_width=True)
