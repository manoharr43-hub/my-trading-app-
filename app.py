# ==========================================
# 🚀 NSE AI PRO V74 - ULTRA AI FULL SYSTEM
# ==========================================

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from io import StringIO
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import pytz

# ==========================================
# CONFIG
# ==========================================
st.set_page_config(page_title="🚀 NSE AI PRO V74", layout="wide")
st.title("🚀 NSE AI PRO V74 - ULTRA AI + BACKTEST")

IST = pytz.timezone("Asia/Kolkata")
st.write("🕒", datetime.now(IST))

# ==========================================
# NSE 200 AUTO FETCH
# ==========================================
@st.cache_data
def get_nse200():
    url = "https://archives.nseindia.com/content/indices/ind_nifty200list.csv"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    df = pd.read_csv(StringIO(res.text))
    return [s + ".NS" for s in df['Symbol'].tolist()]

stocks = get_nse200()

# ==========================================
# INDICATORS
# ==========================================
def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def atr(df, period=14):
    tr = pd.concat([
        df['High'] - df['Low'],
        abs(df['High'] - df['Close'].shift()),
        abs(df['Low'] - df['Close'].shift())
    ], axis=1).max(axis=1)
    return tr.rolling(period).mean()

# ==========================================
# SIGNAL ENGINE
# ==========================================
def generate_trades(df):
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    df['EMA200'] = df['Close'].ewm(span=200).mean()
    df['RSI'] = rsi(df['Close'])
    df['ATR'] = atr(df)
    df['VOL_AVG'] = df['Volume'].rolling(20).mean()

    trades = []

    for i in range(50, len(df)):
        score = 0

        trend = df['EMA50'][i] > df['EMA200'][i]
        volume = df['Volume'][i] > 1.5 * df['VOL_AVG'][i]
        pullback = df['Close'][i] <= df['EMA20'][i]
        momentum = df['RSI'][i] > 55
        volatility = df['ATR'][i] > df['ATR'].rolling(20).mean()[i]

        if trend: score += 25
        if volume: score += 20
        if pullback: score += 20
        if momentum: score += 15
        if volatility: score += 20

        if score >= 55:
            entry = df['Close'][i]
            sl = df['Low'][i-3:i].min()
            target = entry + 2*(entry - sl)

            trades.append({
                "Time": df.index[i],
                "Entry": entry,
                "SL": sl,
                "Target": target,
                "Score": score
            })

    return pd.DataFrame(trades)

# ==========================================
# REAL BACKTEST
# ==========================================
def backtest(df, trades):
    results = []

    for _, t in trades.iterrows():
        entry, sl, target = t['Entry'], t['SL'], t['Target']
        outcome = "OPEN"
        pnl = 0

        for i in range(len(df)):
            if df['High'].iloc[i] >= target:
                outcome = "WIN"
                pnl = target - entry
                break
            elif df['Low'].iloc[i] <= sl:
                outcome = "LOSS"
                pnl = entry - sl
                break

        results.append({
            "Time": t['Time'],
            "Entry": round(entry,2),
            "SL": round(sl,2),
            "Target": round(target,2),
            "Score": t['Score'],
            "Result": outcome,
            "PnL": round(pnl,2)
        })

    return pd.DataFrame(results)

# ==========================================
# PROCESS STOCK
# ==========================================
def process_stock(stock):
    try:
        df = yf.download(stock, period="3mo", interval="15m", progress=False)

        if df.empty:
            return None

        trades = generate_trades(df)

        if trades.empty:
            return None

        bt = backtest(df, trades)
        bt["Stock"] = stock

        return bt

    except:
        return None

# ==========================================
# RUN BUTTON
# ==========================================
if st.button("🚀 RUN NSE 200 ULTRA SYSTEM"):

    all_data = []

    with st.spinner("Scanning NSE 200 + Backtesting..."):
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = executor.map(process_stock, stocks)

        for r in results:
            if r is not None:
                all_data.append(r)

    if all_data:
        final_df = pd.concat(all_data)

        # FILTER
        final_df = final_df[final_df["Score"] >= 55]

        # METRICS
        total = len(final_df)
        wins = len(final_df[final_df["Result"] == "WIN"])
        losses = len(final_df[final_df["Result"] == "LOSS"])
        pnl = final_df["PnL"].sum()
        win_rate = (wins / total) * 100 if total else 0

        st.subheader("📊 PERFORMANCE")
        st.write(f"Trades: {total}")
        st.write(f"Wins: {wins} | Losses: {losses}")
        st.write(f"Win Rate: {round(win_rate,2)}%")
        st.write(f"Total PnL: ₹ {round(pnl,2)}")

        # STRONG SIGNALS
        strong = final_df[final_df["Score"] >= 70]
        st.subheader("🔥 STRONG TRADES")
        st.dataframe(strong, use_container_width=True)

        # ALL DATA
        st.subheader("📋 ALL TRADES")
        st.dataframe(final_df, use_container_width=True)

        # DOWNLOAD
        csv = final_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Report", csv, "nse200_report.csv")

    else:
        st.warning("No trades found")
