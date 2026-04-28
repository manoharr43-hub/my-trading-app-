import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from streamlit_autorefresh import st_autorefresh
import io

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🚀 NSE AI PRO V50", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V50 - FULL DAY SCANNER + SMART BACKTEST")
st.write(f"🕒 Market Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")

# =============================
# STOCKS
# =============================
stocks = ["RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","LT","ITC","AXISBANK","BAJFINANCE"]

# =============================
# FETCH
# =============================
@st.cache_data(ttl=60)
def fetch_data():
    tickers = [s + ".NS" for s in stocks]
    return yf.download(tickers, period="5d", interval="5m", group_by="ticker", progress=False)

data = fetch_data()

def get_df(sym):
    try:
        df = data[sym + ".NS"]
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(0)
        return df.dropna()
    except:
        return None

# =============================
# INDICATORS
# =============================
def indicators(df):
    df = df.copy()

    df["EMA20"] = df["Close"].ewm(span=20).mean()
    df["VWAP"] = (df["Close"] * df["Volume"]).cumsum() / (df["Volume"].cumsum() + 1e-9)

    hl = df["High"] - df["Low"]
    tr = pd.concat([
        hl,
        abs(df["High"] - df["Close"].shift()),
        abs(df["Low"] - df["Close"].shift())
    ], axis=1).max(axis=1)

    df["ATR"] = tr.rolling(14).mean()
    df["VolAvg"] = df["Volume"].rolling(20).mean()

    return df

# =============================
# SUPPORT / RESISTANCE
# =============================
def sr(df):
    support = df["Low"].rolling(20).min()
    resistance = df["High"].rolling(20).max()
    return support, resistance

# =============================
# AI SCORE
# =============================
def ai_score(r):
    score = 0
    if r["Close"] > r["EMA20"]: score += 25
    if r["Close"] > r["VWAP"]: score += 20
    if r["Volume"] > r["VolAvg"] * 2: score += 25
    if r["Close"] > r["Open"]: score += 15
    return min(100, max(0, score))

# =============================
# PULLBACK LOGIC
# =============================
def pullback_signal(row, support, resistance):
    if abs(row["Close"] - row["EMA20"]) / row["EMA20"] < 0.004:

        if row["Close"] > row["VWAP"] and row["Close"] > row["Open"]:
            return "BUY PULLBACK 🟢"
        elif row["Close"] < row["VWAP"] and row["Close"] < row["Open"]:
            return "SELL PULLBACK 🔴"

    return None

# =============================
# EXCEL
# =============================
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

# =============================
# LIVE SCAN (FULL DAY SCAN FIXED)
# =============================
if st.button("🚀 RUN FULL DAY LIVE SCAN"):

    results = []

    for s in stocks:
        df = get_df(s)
        if df is None or len(df) < 50:
            continue

        df = indicators(df)

        support, resistance = sr(df)

        # 🔥 FULL DAY LOOP
        for i in range(20, len(df)):
            row = df.iloc[i]

            signal = pullback_signal(row, support.iloc[i], resistance.iloc[i])

            if signal:

                score = ai_score(row)

                entry = row["Close"]

                results.append({
                    "TIME": df.index[i].strftime("%H:%M"),
                    "STOCK": s,
                    "SIGNAL": signal,
                    "AI_SCORE": score,
                    "SUPPORT": support.iloc[i],
                    "RESISTANCE": resistance.iloc[i],
                    "ENTRY": entry,
                    "SL": entry - row["ATR"]*1.5 if "BUY" in signal else entry + row["ATR"]*1.5,
                    "TARGET": entry + row["ATR"]*3 if "BUY" in signal else entry - row["ATR"]*3
                })

    if results:
        df_res = pd.DataFrame(results)
        df_res = df_res.sort_values("AI_SCORE", ascending=False)

        st.subheader("🏆 FULL DAY SCAN RESULTS")
        st.dataframe(df_res, use_container_width=True)

        st.download_button(
            "📥 DOWNLOAD LIVE SCAN EXCEL",
            data=to_excel(df_res),
            file_name=f"full_scan_{now.strftime('%Y%m%d_%H%M')}.xlsx"
        )
    else:
        st.warning("No signals found")

# =============================
# BACKTEST FIXED (TIME + SR + PULLBACK)
# =============================
st.subheader("📊 BACKTEST SYSTEM")

bt_date = st.date_input(
    "📅 Select Date",
    value=now.date() - timedelta(days=1)
)

if st.button("📊 RUN BACKTEST"):

    logs = []

    for s in stocks:
        df = get_df(s)
        if df is None:
            continue

        df = indicators(df)

        df["DATE"] = pd.to_datetime(df.index).date
        df_day = df[df["DATE"] == bt_date]

        if df_day.empty:
            continue

        support, resistance = sr(df_day)

        for i in range(20, len(df_day)):
            row = df_day.iloc[i]

            signal = pullback_signal(row, support.iloc[i], resistance.iloc[i])

            if signal:

                logs.append({
                    "TIME": df_day.index[i].strftime("%H:%M"),
                    "STOCK": s,
                    "SIGNAL": signal,
                    "SUPPORT": support.iloc[i],
                    "RESISTANCE": resistance.iloc[i],
                    "PRICE": row["Close"]
                })

    if logs:
        df_logs = pd.DataFrame(logs)

        st.subheader("📊 BACKTEST RESULTS")
        st.dataframe(df_logs, use_container_width=True)

        st.download_button(
            "📥 DOWNLOAD BACKTEST",
            data=to_excel(df_logs),
            file_name=f"backtest_{bt_date}.xlsx"
        )
    else:
        st.warning("No backtest data found")
