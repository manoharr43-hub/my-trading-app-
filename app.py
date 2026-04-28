import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
from streamlit_autorefresh import st_autorefresh
import io

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🚀 NSE AI PRO V47", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V47 - BIG PLAYER + AI SYSTEM")
st.write(f"🕒 Market Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")

# =============================
# STOCKS (SIMPLE SAMPLE - YOU CAN EXTEND NSE200)
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

def get_df(symbol):
    try:
        df = data[symbol + ".NS"]
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

    if r["Close"] > r["EMA20"]:
        score += 25
    if r["Close"] > r["VWAP"]:
        score += 20
    if r["Volume"] > r["VolAvg"] * 2:
        score += 25
    if r["Close"] > r["Open"]:
        score += 15
    if r["ATR"] > 0:
        score += 10

    return min(100, max(0, score))

# =============================
# BIG PLAYER LOGIC
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

        if abs(l["Close"] - l["EMA20"]) / l["EMA20"] < 0.004:

            score = ai_score(l)
            big = big_player(l, df)

            signal = "BUY 🟢" if l["Close"] > l["VWAP"] else "SELL 🔴"
            entry = l["Close"]

            results.append({
                "STOCK": s,
                "SIGNAL": signal,
                "AI_SCORE": score,
                "BIG_PLAYER": big,
                "SUPPORT": support,
                "RESISTANCE": resistance,
                "ENTRY": entry,
                "SL": entry - l["ATR"]*1.5 if "BUY" in signal else entry + l["ATR"]*1.5,
                "TARGET": entry + l["ATR"]*3 if "BUY" in signal else entry - l["ATR"]*3
            })

    if results:
        df_res = pd.DataFrame(results)

        # TOP 10
        df_res = df_res.sort_values("AI_SCORE", ascending=False).head(10)

        st.subheader("🏆 TOP 10 STRONG STOCKS")
        st.dataframe(df_res, use_container_width=True)

        st.download_button(
            "📥 DOWNLOAD EXCEL",
            data=to_excel(df_res),
            file_name=f"live_scan_{now.strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    else:
        st.warning("No signals found")
