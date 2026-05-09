import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from concurrent.futures import ThreadPoolExecutor
import io

# =========================
# APP CONFIG
# =========================
st.set_page_config(page_title="🚀 NSE AI V56 PRO", layout="wide")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI V56 PRO - NSE 200 BIG MOVE SYSTEM")
st.markdown(f"🕒 LIVE TIME: {now.strftime('%Y-%m-%d %H:%M:%S')}")

# =========================
# NSE TOP 200 STOCKS (CLEAN SET)
# =========================
def get_stocks():
    return [
        "RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","AXISBANK","KOTAKBANK","LT","ITC",
        "BHARTIARTL","HCLTECH","WIPRO","TECHM","SUNPHARMA","DRREDDY","CIPLA","TITAN",
        "MARUTI","TATAMOTORS","BAJFINANCE","BAJAJFINSV","ADANIENT","ADANIPORTS","NTPC",
        "POWERGRID","ONGC","COALINDIA","JSWSTEEL","TATASTEEL","HINDALCO","GRASIM",
        "ULTRACEMCO","INDUSINDBK","M&M","DIVISLAB","APOLLOHOSP","EICHERMOT",
        "HEROMOTOCO","BRITANNIA","NESTLEIND","DABUR","MARICO","COLPAL",
        "GODREJCP","TATACONSUM","SBILIFE","HDFCLIFE","ICICIPRULI","LICI",
        "PNB","BANKBARODA","CANBK","IDFCFIRSTB","FEDERALBNK","CHOLAFIN",
        "MUTHOOTFIN","SHRIRAMFIN","TRENT","PAGEIND","ALKEM","BIOCON",
        "LUPIN","AUROPHARMA","GLENMARK","TORNTPHARM","DLF","VOLTAS"
    ]

stocks = get_stocks()

# =========================
# DATA
# =========================
@st.cache_data(ttl=300)
def load_data():
    tickers = [s + ".NS" for s in stocks]
    return yf.download(tickers, period="1mo", interval="15m", group_by="ticker", threads=True)

data = load_data()

# =========================
# RSI
# =========================
def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / (avg_loss + 1e-9)
    return 100 - (100 / (1 + rs))

# =========================
# VWAP
# =========================
def vwap(df):
    tp = (df["High"] + df["Low"] + df["Close"]) / 3
    return (tp * df["Volume"]).cumsum() / (df["Volume"].cumsum() + 1e-9)

# =========================
# BIG MOVE ENGINE
# =========================
def big_move_engine(row, prev_row):

    vol_ratio = row["Volume"] / (row["VOL_AVG"] + 1e-9)
    volume_score = 1 if vol_ratio > 2 else 0

    vwap_break = 1 if row["Close"] > row["VWAP"] else 0
    atr_expand = 1 if row["ATR"] > prev_row["ATR"] else 0
    rsi_mom = 1 if row["RSI"] > 55 else 0
    breakout = 1 if row["Close"] > prev_row["Close"] else 0

    score = (
        volume_score * 30 +
        vwap_break * 25 +
        atr_expand * 20 +
        rsi_mom * 15 +
        breakout * 10
    )

    return score, vol_ratio

# =========================
# ENGINE
# =========================
def engine(stock, raw, date):

    key = stock + ".NS"

    if key not in raw.columns.get_level_values(0):
        return []

    df = raw[key].dropna().copy()
    if len(df) < 60:
        return []

    # indicators
    df["EMA21"] = df["Close"].ewm(span=21).mean()
    df["VWAP"] = vwap(df)
    df["RSI"] = rsi(df["Close"])
    df["VOL_AVG"] = df["Volume"].rolling(20).mean()

    tr = pd.concat([
        df["High"] - df["Low"],
        abs(df["High"] - df["Close"].shift()),
        abs(df["Low"] - df["Close"].shift())
    ], axis=1).max(axis=1)

    df["ATR"] = tr.rolling(14).mean()

    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")

    df.index = df.index.tz_convert(IST)
    df = df[df.index.date == pd.to_datetime(date).date()]

    results = []

    for i in range(1, len(df)):

        row = df.iloc[i]
        prev_row = df.iloc[i-1]

        t = row.name.time()

        if not (datetime.strptime("09:30","%H:%M").time() <= t <= datetime.strptime("14:45","%H:%M").time()):
            continue

        # BIG MOVE SCORE
        big_score, vol_ratio = big_move_engine(row, prev_row)

        # BUY / SELL LOGIC
        buy = (
            row["Close"] > row["VWAP"] and
            55 <= row["RSI"] <= 70 and
            big_score > 60
        )

        sell = (
            row["Close"] < row["VWAP"] and
            30 <= row["RSI"] <= 45 and
            big_score > 60
        )

        if not (buy or sell):
            continue

        signal = "BUY" if buy else "SELL"
        entry = row["Close"]
        atr = row["ATR"]

        if pd.isna(atr):
            continue

        sl = entry - atr * 2.2 if buy else entry + atr * 2.2
        tgt = entry + atr * 2.5 if buy else entry - atr * 2.5

        # BACKTEST
        future = df.iloc[i+1:i+10]
        status = "OPEN"

        for _, f in future.iterrows():
            if buy:
                if f["High"] >= tgt:
                    status = "TARGET"; break
                if f["Low"] <= sl:
                    status = "SL"; break
            else:
                if f["Low"] <= tgt:
                    status = "TARGET"; break
                if f["High"] >= sl:
                    status = "SL"; break

        results.append({
            "TIME": row.name.strftime("%H:%M"),
            "STOCK": stock,
            "SIGNAL": signal,
            "ENTRY": round(entry, 2),
            "SL": round(sl, 2),
            "TARGET": round(tgt, 2),
            "RSI": round(row["RSI"], 2),
            "BIG_MOVE_SCORE": big_score,
            "VOLUME_RATIO": round(vol_ratio, 2),
            "STATUS": status
        })

    return results

# =========================
# EXCEL
# =========================
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

# =========================
# UI
# =========================
tab1, tab2 = st.tabs(["🔥 LIVE SCANNER", "📊 BACKTEST"])

with tab1:

    if st.button("RUN LIVE SCAN"):

        results = []
        with ThreadPoolExecutor(max_workers=10) as ex:
            for r in ex.map(lambda s: engine(s, data, now.date()), stocks):
                results.extend(r)

        df = pd.DataFrame(results)

        if not df.empty:
            df = df.sort_values("BIG_MOVE_SCORE", ascending=False)

            st.subheader("🚀 TOP BIG MOVE STOCKS")
            st.dataframe(df.head(10))

            st.dataframe(df)

            st.download_button("⬇️ DOWNLOAD", to_excel(df), "v56_live.xlsx")
        else:
            st.warning("NO SIGNALS")

with tab2:

    d = st.date_input("Select Date", now.date() - timedelta(days=1))

    if st.button("RUN BACKTEST"):

        results = []
        with ThreadPoolExecutor(max_workers=10) as ex:
            for r in ex.map(lambda s: engine(s, data, d), stocks):
                results.extend(r)

        df = pd.DataFrame(results)

        if not df.empty:
            st.dataframe(df)

            wins = len(df[df["STATUS"] == "TARGET"])
            losses = len(df[df["STATUS"] == "SL"])

            st.success(f"WINS: {wins} | LOSSES: {losses}")

            st.download_button("⬇️ DOWNLOAD", to_excel(df), "v56_backtest.xlsx")
        else:
            st.warning("NO DATA")
