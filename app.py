import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time
import pytz
from streamlit_autorefresh import st_autorefresh
import io

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🚀 NSE AI PRO V57", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V57 - SMART MONEY CLEAN ENGINE")

st.info(f"🕒 TIME: {now.strftime('%H:%M:%S')} IST")

# =============================
# MARKET TIME CHECK
# =============================
def market_open():
    t = datetime.now(IST).time()
    return time(9,15) <= t <= time(15,30)

if market_open():
    st.success("🟢 MARKET OPEN")
else:
    st.error("🔴 MARKET CLOSED")

# =============================
# STOCKS
# =============================
stocks = ["RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","LT","ITC","AXISBANK","BAJFINANCE"]

# =============================
# DATA FETCH
# =============================
@st.cache_data(ttl=60)
def fetch():
    tickers = [s + ".NS" for s in stocks]
    return yf.download(tickers, period="5d", interval="5m", group_by="ticker", progress=False)

data = fetch()

def get_df(s):
    try:
        df = data[s + ".NS"]
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
    return df["Low"].rolling(20).min(), df["High"].rolling(20).max()

# =============================
# STRONG CANDLE FILTER
# =============================
def strong_candle(r):
    body = abs(r["Close"] - r["Open"])
    range_ = r["High"] - r["Low"]

    if range_ == 0:
        return False

    return (body / range_) > 0.4

# =============================
# SIGNAL (CLEAN VERSION)
# =============================
def signal(r):
    if not strong_candle(r):
        return None

    if r["Close"] > r["EMA20"] and r["Close"] > r["VWAP"]:
        return "BUY 🟢"

    if r["Close"] < r["EMA20"] and r["Close"] < r["VWAP"]:
        return "SELL 🔴"

    return None

# =============================
# BIG PLAYER (REAL LOGIC)
# =============================
def big_player(r, high, low):
    if r["Volume"] > r["VolAvg"] * 2.2:
        if r["Close"] > high:
            return "🔥 BREAKOUT BUY"
        elif r["Close"] < low:
            return "🔴 BREAKDOWN SELL"
        else:
            return "⚡ ACCUMULATION"
    return "-"

# =============================
# SAFE TIME
# =============================
def safe_time(t):
    t = pd.to_datetime(t)
    if t.tz is None:
        t = t.tz_localize("UTC")
    t = t.tz_convert("Asia/Kolkata")
    return t.strftime("%H:%M")

# =============================
# EXCEL
# =============================
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

# =============================
# LIVE SCANNER (NO DUPLICATES)
# =============================
if market_open():

    if st.button("🚀 RUN LIVE SCANNER"):

        results = []
        last_trade = {}

        for s in stocks:
            df = get_df(s)
            if df is None or len(df) < 50:
                continue

            df = indicators(df)
            support, resistance = sr(df)

            last_trade[s] = None

            for i in range(20, len(df)):
                row = df.iloc[i]

                sig = signal(row)

                if sig:

                    trend = "BUY" if sig.startswith("BUY") else "SELL"

                    # 🔥 NO DUPLICATE TRADE
                    if last_trade[s] == trend:
                        continue

                    last_trade[s] = trend

                    results.append({
                        "TIME": safe_time(df.index[i]),
                        "STOCK": s,
                        "SIGNAL": sig,
                        "BIG_PLAYER": big_player(row, resistance.iloc[i], support.iloc[i]),
                        "ENTRY": row["Close"],
                        "SUPPORT": support.iloc[i],
                        "RESISTANCE": resistance.iloc[i],
                        "SL": row["Close"] - row["ATR"]*1.5 if trend=="BUY" else row["Close"] + row["ATR"]*1.5,
                        "TARGET": row["Close"] + row["ATR"]*3 if trend=="BUY" else row["Close"] - row["ATR"]*3
                    })

        if results:
            df_res = pd.DataFrame(results)

            st.subheader("🏆 CLEAN LIVE SCANNER RESULTS")
            st.dataframe(df_res, use_container_width=True)

            st.download_button(
                "📥 DOWNLOAD LIVE EXCEL",
                data=to_excel(df_res),
                file_name=f"live_{now.strftime('%Y%m%d_%H%M')}.xlsx"
            )
        else:
            st.warning("No strong signals found")

else:
    st.error("⛔ MARKET CLOSED")

# =============================
# BACKTEST CLEAN SYSTEM
# =============================
st.subheader("📊 BACKTEST SYSTEM")

bt_date = st.date_input("📅 Select Date", value=now.date() - timedelta(days=1))

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

        last_trade = None

        for i in range(20, len(df_day)):
            row = df_day.iloc[i]

            sig = signal(row)

            if sig:

                trend = "BUY" if sig.startswith("BUY") else "SELL"

                if last_trade == trend:
                    continue

                last_trade = trend

                logs.append({
                    "TIME": safe_time(df_day.index[i]),
                    "STOCK": s,
                    "SIGNAL": sig,
                    "BIG_PLAYER": big_player(row, resistance.iloc[i], support.iloc[i]),
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
