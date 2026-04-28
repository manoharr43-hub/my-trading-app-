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
st.set_page_config(page_title="🚀 NSE AI PRO V49", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V49 - SMART MONEY AI SYSTEM")
st.write(f"🕒 Market Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")

# =============================
# STOCK LIST
# =============================
stocks = [
    "RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK",
    "SBIN","LT","ITC","AXISBANK","BAJFINANCE"
]

# =============================
# FETCH DATA
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
    support = df["Low"].rolling(20).min().iloc[-1]
    resistance = df["High"].rolling(20).max().iloc[-1]
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
    if r["ATR"] > 0: score += 10
    return min(100, max(0, score))

# =============================
# BIG PLAYER
# =============================
def big_player(r, df):
    support, resistance = sr(df)

    if r["Volume"] > r["VolAvg"] * 2.5 and r["Close"] > resistance:
        return "🔥 BIG BUY BREAKOUT"
    elif r["Volume"] > r["VolAvg"] * 2.5 and r["Close"] < support:
        return "🔴 BIG SELL BREAKDOWN"
    elif r["Volume"] > r["VolAvg"] * 2:
        return "⚡ ACCUMULATION"
    else:
        return "-"

# =============================
# EXCEL
# =============================
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

# =============================
# LIVE SCAN
# =============================
if st.button("🚀 RUN LIVE SCAN"):

    results = []

    for s in stocks:
        df = get_df(s)
        if df is None or len(df) < 50:
            continue

        df = indicators(df)
        l = df.iloc[-1]

        support, resistance = sr(df)

        dist = abs(l["Close"] - l["EMA20"]) / l["EMA20"]

        if dist < 0.004:

            score = ai_score(l)
            big = big_player(l, df)

            signal = "BUY 🟢" if l["Close"] > l["VWAP"] else "SELL 🔴"
            entry = float(l["Close"])

            sl = entry - l["ATR"]*1.5 if "BUY" in signal else entry + l["ATR"]*1.5
            tgt = entry + l["ATR"]*3 if "BUY" in signal else entry - l["ATR"]*3

            results.append({
                "TIME": now.strftime("%H:%M"),
                "STOCK": s,
                "SIGNAL": signal,
                "AI_SCORE": score,
                "BIG_PLAYER": big,
                "SUPPORT": support,
                "RESISTANCE": resistance,
                "ENTRY": entry,
                "SL": sl,
                "TARGET": tgt
            })

    if results:
        df_res = pd.DataFrame(results)
        df_res = df_res.sort_values("AI_SCORE", ascending=False).head(10)

        st.subheader("🏆 TOP 10 STOCKS")
        st.dataframe(df_res, use_container_width=True)

        st.download_button(
            "📥 DOWNLOAD LIVE EXCEL",
            data=to_excel(df_res),
            file_name=f"live_{now.strftime('%Y%m%d_%H%M')}.xlsx"
        )
    else:
        st.warning("No signals found")

# =============================
# BACKTEST (FIXED DATE SELECT)
# =============================
st.subheader("📊 BACKTEST SECTION")

bt_date = st.date_input(
    "📅 Select Backtest Date",
    value=now.date() - timedelta(days=1),
    min_value=now.date() - timedelta(days=30),
    max_value=now.date()
)

st.info(f"Selected Date: {bt_date}")

if st.button("📊 RUN BACKTEST"):

    logs = []

    for s in stocks:
        df = get_df(s)
        if df is None:
            continue

        df = indicators(df)

        # FIX DATE FILTER
        df["DATE"] = pd.to_datetime(df.index).date
        df_day = df[df["DATE"] == bt_date]

        if df_day.empty:
            continue

        for i in range(20, len(df_day)):
            row = df_day.iloc[i]

            score = ai_score(row)

            if score > 70:
                logs.append({
                    "TIME": df_day.index[i].strftime("%H:%M"),
                    "STOCK": s,
                    "AI_SCORE": score,
                    "PRICE": row["Close"]
                })

    if logs:
        df_logs = pd.DataFrame(logs)

        st.dataframe(df_logs, use_container_width=True)

        st.download_button(
            "📥 DOWNLOAD BACKTEST EXCEL",
            data=to_excel(df_logs),
            file_name=f"backtest_{bt_date}.xlsx"
        )
    else:
        st.warning("No backtest data found")
