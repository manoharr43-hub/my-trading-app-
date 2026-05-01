import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta, time
import pytz

# ==========================================
# CONFIG
# ==========================================
st.set_page_config(page_title="🚀 NSE AI PRO V71", layout="wide")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V71 – STABLE PRO VERSION")
st.write(f"🕒 {now.strftime('%Y-%m-%d %H:%M:%S')}")

# ==========================================
# NSE STOCKS (you can paste full 200)
# ==========================================
stocks = [
    "RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK",
    "SBIN","ITC","LT","AXISBANK","KOTAKBANK"
]

tickers = [s + ".NS" for s in stocks]

# ==========================================
# DATA
# ==========================================
@st.cache_data(ttl=300)
def load_data():
    return yf.download(
        tickers,
        period="15d",
        interval="5m",
        group_by="ticker",
        threads=True
    )

# ==========================================
# INDICATORS
# ==========================================
def add_indicators(df):
    df = df.copy()

    df["EMA20"] = df["Close"].ewm(span=20).mean()
    df["EMA50"] = df["Close"].ewm(span=50).mean()
    df["VOLAVG"] = df["Volume"].rolling(20).mean()

    delta = df["Close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rs = gain / loss

    df["RSI"] = 100 - (100 / (1 + rs))

    return df

# ==========================================
# SIGNAL ENGINE
# ==========================================
def signal_engine(row):
    sig, entry, sl, tgt, typ = None, None, None, None, None

    # Pullback Buy
    if row["Close"] > row["EMA20"] and row["Low"] <= row["EMA20"]:
        if row["EMA20"] > row["EMA50"]:
            sig = "BUY"
            typ = "PULLBACK"
            entry = row["Close"]
            sl = row["EMA20"] * 0.995
            tgt = entry + (entry - sl) * 2

    # Pullback Sell
    elif row["Close"] < row["EMA20"] and row["High"] >= row["EMA20"]:
        if row["EMA20"] < row["EMA50"]:
            sig = "SELL"
            typ = "PULLBACK"
            entry = row["Close"]
            sl = row["EMA20"] * 1.005
            tgt = entry - (sl - entry) * 2

    # Big Player
    if row["Volume"] > row["VOLAVG"] * 2:
        if row["Close"] > row["EMA20"]:
            sig = "BUY"
            typ = "BIG PLAYER"
            entry = row["Close"]
            sl = row["Low"]
            tgt = entry + (entry - sl) * 2.5

        elif row["Close"] < row["EMA20"]:
            sig = "SELL"
            typ = "BIG PLAYER"
            entry = row["Close"]
            sl = row["High"]
            tgt = entry - (sl - entry) * 2.5

    return sig, entry, sl, tgt, typ

# ==========================================
# SCORE
# ==========================================
def calc_score(row):
    score = 0

    if row["Close"] > row["EMA20"]:
        score += 2

    if row["Volume"] > row["VOLAVG"]:
        score += 2

    if 40 < row["RSI"] < 60:
        score += 2

    return score

# ==========================================
# MARKET TIME
# ==========================================
def is_market_open(ts):
    return time(9, 15) <= ts.time() <= time(15, 30)

# ==========================================
# UI
# ==========================================
tab1, tab2 = st.tabs(["🚀 LIVE SCANNER", "📊 BACKTEST"])

# ==========================================
# LIVE SCANNER
# ==========================================
with tab1:
    if st.button("RUN LIVE SCAN"):
        data = load_data()
        results = []

        for s in stocks:
            t = s + ".NS"

            if t not in data.columns.levels[0]:
                continue

            df = data[t].dropna()
            if len(df) < 50:
                continue

            df = add_indicators(df)

            row = df.iloc[-1]
            ts = df.index[-1].tz_convert(IST)

            if not is_market_open(ts):
                continue

            sig, entry, sl, tgt, typ = signal_engine(row)
            score = calc_score(row)

            if sig and score >= 4:
                results.append({
                    "TIME": ts.strftime("%H:%M"),
                    "STOCK": s,
                    "TYPE": typ,
                    "SIGNAL": sig,
                    "ENTRY": round(entry,2),
                    "SL": round(sl,2),
                    "TARGET": round(tgt,2),
                    "SCORE": score
                })

        if results:
            df_live = pd.DataFrame(results)
            st.dataframe(df_live, use_container_width=True)

            csv = df_live.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download Live", csv, "live_signals.csv")

        else:
            st.warning("No signals found")

# ==========================================
# BACKTEST
# ==========================================
with tab2:
    test_date = st.date_input("Select Backtest Date", now.date() - timedelta(days=1))

    if st.button("RUN BACKTEST"):
        data = load_data()
        results = []

        for s in stocks:
            t = s + ".NS"

            if t not in data.columns.levels[0]:
                continue

            df = data[t].dropna()
            df.index = df.index.tz_convert(IST)

            df = df[df.index.date == test_date]

            if len(df) < 30:
                continue

            df = add_indicators(df)

            for i in range(1, len(df)-1):
                row = df.iloc[i]
                ts = df.index[i]

                sig, entry, sl, tgt, typ = signal_engine(row)
                score = calc_score(row)

                if not sig or score < 4:
                    continue

                result = "OPEN"
                exit_price = None

                for j in range(i+1, len(df)):
                    future = df.iloc[j]

                    if sig == "BUY":
                        if future["Low"] <= sl:
                            result = "LOSS"
                            exit_price = sl
                            break
                        if future["High"] >= tgt:
                            result = "WIN"
                            exit_price = tgt
                            break

                    elif sig == "SELL":
                        if future["High"] >= sl:
                            result = "LOSS"
                            exit_price = sl
                            break
                        if future["Low"] <= tgt:
                            result = "WIN"
                            exit_price = tgt
                            break

                if result == "OPEN":
                    exit_price = df.iloc[-1]["Close"]

                rr = abs((exit_price - entry) / (entry - sl)) if (entry - sl) != 0 else 0

                results.append({
                    "TIME": ts.strftime("%H:%M"),
                    "STOCK": s,
                    "TYPE": typ,
                    "SIGNAL": sig,
                    "ENTRY": round(entry,2),
                    "EXIT": round(exit_price,2),
                    "RESULT": result,
                    "R:R": round(rr,2),
                    "SCORE": score
                })

        if results:
            df_bt = pd.DataFrame(results)
            st.dataframe(df_bt, use_container_width=True)

            wins = len(df_bt[df_bt.RESULT=="WIN"])
            losses = len(df_bt[df_bt.RESULT=="LOSS"])
            total = len(df_bt)

            acc = (wins/(wins+losses))*100 if (wins+losses)>0 else 0
            avg_rr = df_bt["R:R"].mean()

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Trades", total)
            c2.metric("Wins ✅", wins)
            c3.metric("Accuracy 🎯", f"{round(acc,2)}%")
            c4.metric("Avg R:R", round(avg_rr,2))

            csv = df_bt.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download Backtest", csv, "backtest.csv")

        else:
            st.warning("No trades found")
