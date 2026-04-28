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
st.set_page_config(page_title="🚀 NSE AI PRO V45 FULL SCAN", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V45 - FULL NSE SCAN ENGINE")
st.write(f"🕒 Market Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")

# =============================
# FULL NSE 200 (SAFE VERSION SAMPLE - expand anytime)
# =============================
stocks = [
    "RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","ITC",
    "LT","AXISBANK","BHARTIARTL","TATAMOTORS","MARUTI",
    "ADANIENT","ADANIPORTS","BAJFINANCE","KOTAKBANK","HCLTECH",
    "WIPRO","SUNPHARMA","ULTRACEMCO","ONGC","POWERGRID",
    "NTPC","JSWSTEEL","TATASTEEL","COALINDIA","HINDALCO",
    "EICHERMOT","HEROMOTOCO","DRREDDY","CIPLA","DIVISLAB",
    "APOLLOHOSP","BRITANNIA","NESTLEIND","TECHM","LTIM"
]

# =============================
# INDICATORS
# =============================
def add_indicators(df):
    df = df.copy()

    if len(df) < 25:
        return df

    df["EMA20"] = df["Close"].ewm(span=20).mean()
    df["VWAP"] = (df["Close"] * df["Volume"]).cumsum() / (df["Volume"].cumsum() + 1e-9)

    high_low = df["High"] - df["Low"]
    tr = pd.concat([
        high_low,
        abs(df["High"] - df["Close"].shift()),
        abs(df["Low"] - df["Close"].shift())
    ], axis=1).max(axis=1)

    df["ATR"] = tr.rolling(14).mean()
    df["VolAvg"] = df["Volume"].rolling(20).mean()

    return df

# =============================
# DATA FETCH (FAST MODE)
# =============================
@st.cache_data(ttl=60)
def fetch_data(symbols):
    tickers = [s + ".NS" for s in symbols]

    return yf.download(
        tickers,
        period="5d",
        interval="5m",
        group_by="ticker",
        progress=False,
        threads=True
    )

data = fetch_data(stocks)

# =============================
# SAFE SYMBOL EXTRACT
# =============================
def get_df(symbol):
    try:
        key = symbol + ".NS"
        if key in data.columns.levels[0]:
            df = data[key].dropna()
            return df
    except:
        pass
    return None

# =============================
# EXCEL EXPORT
# =============================
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="REPORT")
    return output.getvalue()

# =============================
# TABS
# =============================
tab1, tab2 = st.tabs(["🔥 LIVE FULL NSE SCAN", "📊 BACKTEST ENGINE"])

# =============================
# LIVE SCAN (TOP SIGNAL ONLY)
# =============================
with tab1:
    if st.button("RUN FULL NSE SCAN"):

        results = []

        for s in stocks:

            df = get_df(s)
            if df is None or df.empty:
                continue

            try:
                df = add_indicators(df)
                l = df.iloc[-1]

                if pd.isna(l["EMA20"]):
                    continue

                dist = abs(l["Close"] - l["EMA20"]) / l["EMA20"]

                # relaxed filter (IMPORTANT FOR FULL NSE)
                if dist < 0.006:

                    signal = None

                    if l["Close"] > l["VWAP"] and l["Close"] > l["Open"]:
                        signal = "BUY 🟢"
                    elif l["Close"] < l["VWAP"] and l["Close"] < l["Open"]:
                        signal = "SELL 🔴"

                    if signal:

                        entry = float(l["Close"])
                        atr = l["ATR"] if not np.isnan(l["ATR"]) else 1

                        score = 1
                        if l["Volume"] > l["VolAvg"] * 2:
                            score += 1
                        if dist < 0.003:
                            score += 1

                        results.append({
                            "TIME": df.index[-1].strftime("%H:%M"),
                            "STOCK": s,
                            "SIGNAL": signal,
                            "ENTRY": round(entry, 2),
                            "SL": round(entry - atr*1.5 if "BUY" in signal else entry + atr*1.5, 2),
                            "TARGET": round(entry + atr*3 if "BUY" in signal else entry - atr*3, 2),
                            "BIG PLAYER": "🔥 YES" if l["Volume"] > l["VolAvg"]*2 else "-",
                            "SCORE": score
                        })

            except:
                continue

        if results:

            df_res = pd.DataFrame(results)

            # SORT = BEST SIGNAL FIRST
            df_res = df_res.sort_values(by="SCORE", ascending=False)

            st.success(f"🔥 Total Signals: {len(df_res)}")
            st.dataframe(df_res, use_container_width=True)

        else:
            st.warning("No strong signals in FULL NSE scan")

# =============================
# BACKTEST ENGINE (SAFE)
# =============================
with tab2:

    bt_date = st.date_input("Select Date", value=now.date() - timedelta(days=1))

    if st.button("RUN BACKTEST FULL NSE"):

        logs = []

        for s in stocks:

            df = get_df(s)
            if df is None or df.empty:
                continue

            try:
                df = add_indicators(df)
                df.index = pd.to_datetime(df.index)

                day = df[df.index.date == bt_date]

                if day.empty:
                    continue

                last = None

                for i in range(25, len(day)):

                    r = day.iloc[i]
                    t = day.index[i]

                    dist = abs(r["Close"] - r["EMA20"]) / r["EMA20"]

                    if dist < 0.006:

                        sig = None

                        if r["Close"] > r["VWAP"] and r["Close"] > r["Open"]:
                            sig = "BUY"
                        elif r["Close"] < r["VWAP"] and r["Close"] < r["Open"]:
                            sig = "SELL"

                        if sig and sig != last:

                            atr = r["ATR"] if not np.isnan(r["ATR"]) else 1
                            entry = float(r["Close"])

                            logs.append({
                                "TIME": t.strftime("%H:%M"),
                                "STOCK": s,
                                "TYPE": sig,
                                "ENTRY": round(entry, 2),
                                "SL": round(entry - atr*1.5 if sig=="BUY" else entry + atr*1.5, 2),
                                "TARGET": round(entry + atr*3 if sig=="BUY" else entry - atr*3, 2),
                                "BIG PLAYER": "🔥" if r["Volume"] > r["VolAvg"]*2 else "-"
                            })

                            last = sig

            except:
                continue

        if logs:

            df_logs = pd.DataFrame(logs)

            st.dataframe(df_logs, use_container_width=True)

            st.download_button(
                "📥 DOWNLOAD EXCEL",
                data=to_excel(df_logs),
                file_name=f"FULL_NSE_BACKTEST_{bt_date}.xlsx"
            )

        else:
            st.warning("No backtest signals found")
