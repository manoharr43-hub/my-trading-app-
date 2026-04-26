import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="🔥 NSE LIVE SCANNER", layout="wide")
st.title("🚀 NSE AI PRO V45 – LIVE SCANNER")

# =============================
# STOCK DATABASE (ALL SECTORS)
# =============================
stocks = [
    "HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","AXISBANK.NS",
    "RELIANCE.NS","ONGC.NS",
    "INFY.NS","TCS.NS","WIPRO.NS",
    "ITC.NS","HINDUNILVR.NS",
    "TATAMOTORS.NS","MARUTI.NS"
]

interval = st.selectbox("🕒 Timeframe", ["5m","15m"])

# =============================
# FUNCTION
# =============================
def analyze_stock(symbol):
    try:
        df = yf.download(symbol, period="1d", interval=interval, progress=False)

        if df.empty:
            return None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df.dropna().reset_index()

        # EMA
        df["EMA9"] = df["Close"].ewm(span=9).mean()
        df["EMA21"] = df["Close"].ewm(span=21).mean()

        # RSI
        delta = df["Close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        rs = gain.rolling(14).mean() / loss.rolling(14).mean()
        df["RSI"] = 100 - (100/(1+rs))
        df["RSI"] = df["RSI"].fillna(50)

        # VWAP
        df["VWAP"] = (df["Volume"]*(df["High"]+df["Low"]+df["Close"])/3).cumsum()/df["Volume"].cumsum()

        # Volume spike
        df["Vol_Avg"] = df["Volume"].rolling(20).mean().fillna(0)
        df["Big"] = df["Volume"] > df["Vol_Avg"]*2

        latest = df.iloc[-1]

        # SIGNAL LOGIC
        buy = (
            latest["EMA9"] > latest["EMA21"] and
            latest["Close"] > latest["VWAP"] and
            latest["RSI"] > 60 and
            latest["Big"]
        )

        sell = (
            latest["EMA9"] < latest["EMA21"] and
            latest["Close"] < latest["VWAP"] and
            latest["RSI"] < 40 and
            latest["Big"]
        )

        reversal = (
            df["EMA9"].iloc[-2] < df["EMA21"].iloc[-2] and latest["EMA9"] > latest["EMA21"]
        ) or (
            df["EMA9"].iloc[-2] > df["EMA21"].iloc[-2] and latest["EMA9"] < latest["EMA21"]
        )

        signal = ""
        if buy:
            signal = "🔥 STRONG BUY"
        elif sell:
            signal = "❌ STRONG SELL"
        elif reversal:
            signal = "🔄 REVERSAL"

        if signal == "":
            return None

        entry = latest["Close"]

        if "BUY" in signal:
            sl = entry * 0.995
            target = entry * 1.015
        elif "SELL" in signal:
            sl = entry * 1.005
            target = entry * 0.985
        else:
            sl = entry * 0.997
            target = entry * 1.01

        return {
            "Stock": symbol,
            "Signal
