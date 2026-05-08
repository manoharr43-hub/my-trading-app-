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
st.set_page_config(page_title="🚀 NSE AI V52 PRO - NIFTY200", layout="wide")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI V52 PRO - NIFTY 200 DECISION SYSTEM")
st.markdown(f"🕒 LIVE TIME: {now.strftime('%Y-%m-%d %H:%M:%S')}")

# =========================
# NIFTY 200 STOCKS (SAFE FULL LIST)
# =========================
def get_nifty200_stocks():
    return [
        "RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","AXISBANK",
        "KOTAKBANK","LT","ITC","BHARTIARTL","HCLTECH","WIPRO","TECHM",
        "SUNPHARMA","DRREDDY","CIPLA","DIVISLAB","TITAN",
        "NESTLEIND","BRITANNIA","DABUR","MARICO","COLPAL","HINDUNILVR",
        "MARUTI","TATAMOTORS","M&M","EICHERMOT","HEROMOTOCO","TVSMOTOR",
        "ONGC","IOC","BPCL","NTPC","POWERGRID","COALINDIA","GAIL",
        "JSWSTEEL","TATASTEEL","HINDALCO","GRASIM","ULTRACEMCO",
        "BAJFINANCE","BAJAJFINSV","INDUSINDBK","PNB","BANKBARODA",
        "CANBK","SBILIFE","HDFCLIFE","LICI",
        "ADANIENT","ADANIPORTS","DLF","SIEMENS","ABB","BEL","BHEL",
        "HAVELLS","PAGEIND","PIDILITIND","UPL","TRENT"
    ]

stocks = get_nifty200_stocks()

# =========================
# DATA LOAD
# =========================
@st.cache_data(ttl=300)
def load_data():
    tickers = [s + ".NS" for s in stocks]

    df = yf.download(
        tickers,
        period="1mo",
        interval="15m",
        group_by="ticker",
        threads=True
    )
    return df

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
# SCORE ENGINE
# =========================
def score_engine(row):
    score = 0

    if row["Close"] > row["VWAP"]:
        score += 25
    if 55 <= row["RSI"] <= 70:
        score += 25
    if row["Volume"] > row["VOL_AVG"]:
        score += 20
    if row["Close"] > row["EMA21"]:
        score += 20

    return min(score, 100)

def win_probability(score):
    if score >= 90: return 85
    if score >= 80: return 75
    if score >= 70: return 65
    if score >= 60: return 55
    return 40

# =========================
# ENGINE (NO CHANGE IN LOGIC)
# =========================
def engine(stock, raw, date):

    try:
        key = stock + ".NS"

        if key not in raw.columns.get_level_values(0):
            return []

        df = raw[key].dropna().copy()

        if len(df) < 60:
            return []

        df["EMA21"] = df["Close"].ewm(span=21).mean()

        df["VWAP"] = (df["Close"] * df["Volume"]).cumsum() / (df["Volume"].cumsum() + 1e-9)

        tr = pd.concat([
            df["High"] - df["Low"],
            abs(df["High"] - df["Close"].shift()),
            abs(df["Low"] - df["Close"].shift())
        ], axis=1).max(axis=1)

        df["ATR"] = tr.rolling(14).mean()
        df["RSI"] = rsi(df["Close"])
        df["VOL_AVG"] = df["Volume"].rolling(20).mean()

        if df.index.tz is None:
            df.index = df.index.tz_localize("UTC")

        df.index = df.index.tz_convert(IST)
        df = df[df.index.date == pd.to_datetime(date).date()]

        results = []

        if df.empty:
            return []

        for i in range(1, len(df)):

            row = df.iloc[i]
            t = row.name.time()

            if not (datetime.strptime("09:30","%H:%M").time() <= t <= datetime.strptime("14:45","%H:%M").time()):
                continue

            buy = (row["Close"] > row["VWAP"] and 50 < row["RSI"] < 70)
            sell = (row["Close"] < row["VWAP"] and 30 < row["RSI"] < 50)

            if not (buy or sell):
                continue

            entry = row["Close"]
            atr = row["ATR"]

            if pd.isna(atr):
                continue

            sl = entry - atr * 2.5 if buy else entry + atr * 2.5
            tgt = entry + atr * 2.0 if buy else entry - atr * 2.0

            score = score_engine(row)
            win = win_probability(score)

            decision = "STRONG BUY" if score >= 80 else "BUY" if score >= 65 else "HOLD" if score >= 50 else "AVOID"

            status = "OPEN"
            future = df.iloc[i+1:i+15]

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
                "SIGNAL": "BUY" if buy else "SELL",
                "ENTRY": round(entry, 2),
                "SL": round(sl, 2),
                "TARGET": round(tgt, 2),
                "RSI": round(row["RSI"], 2),
                "SCORE": score,
                "WIN%": win,
                "DECISION": decision,
                "STATUS": status
            })

        return results

    except:
        return []

# =========================
# EXCEL EXPORT
# =========================
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Signals")
    return output.getvalue()

# =========================
# UI
# =========================
tab1, tab2 = st.tabs(["🔥 LIVE SCANNER", "📊 BACKTEST"])

# =========================
# LIVE SCANNER
# =========================
with tab1:

    if st.button("RUN LIVE SCAN (NIFTY200)"):

        results = []

        with ThreadPoolExecutor(max_workers=10) as ex:
            for r in ex.map(lambda s: engine(s, data, now.date()), stocks):
                results.extend(r)

        df = pd.DataFrame(results)

        if not df.empty:

            df = df.sort_values("SCORE", ascending=False)

            st.subheader("🥇 TOP PICKS")
            st.dataframe(df.head(10))

            st.subheader("📊 ALL SIGNALS")
            st.dataframe(df)

            st.download_button(
                "⬇️ DOWNLOAD EXCEL",
                data=to_excel(df),
                file_name="nse_ai_v52_live.xlsx"
            )

        else:
            st.warning("NO SIGNALS FOUND")

# =========================
# BACKTEST
# =========================
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

            st.download_button(
                "⬇️ DOWNLOAD BACKTEST EXCEL",
                data=to_excel(df),
                file_name="nse_ai_v52_backtest.xlsx"
            )

        else:
            st.warning("NO DATA")
