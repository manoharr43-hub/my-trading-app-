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
st.set_page_config(page_title="🚀 NSE AI PRO V45", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V45 - LIVE + BACKTEST + BIG PLAYER")

st.write(f"🕒 Market Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")

# =============================
# STOCKS (LIGHT FOR SPEED)
# =============================
stocks = [
    "RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN",
    "LT","ITC","AXISBANK","KOTAKBANK","HINDUNILVR","TATAMOTORS",
    "BAJFINANCE","MARUTI","SUNPHARMA","WIPRO","ONGC","NTPC"
]

# =============================
# INDICATORS
# =============================
def add_indicators(df):
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
    df["VolSpike"] = df["Volume"] / (df["VolAvg"] + 1e-9)

    return df

# =============================
# DATA FETCH
# =============================
@st.cache_data(ttl=60)
def load_data():
    tickers = [s + ".NS" for s in stocks]
    return yf.download(tickers, period="5d", interval="5m", group_by="ticker")

data = load_data()

# =============================
# EXCEL EXPORT
# =============================
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

# =============================
# TABS
# =============================
tab1, tab2 = st.tabs(["🔍 LIVE SCANNER", "📊 BACKTEST"])

# =============================
# LIVE SCANNER
# =============================
with tab1:
    if st.button("RUN LIVE SCAN"):
        results = []

        for s in stocks:
            try:
                df = data.get(s + ".NS")
                if df is None or df.empty:
                    continue

                df = add_indicators(df.dropna())
                l = df.iloc[-1]

                dist = abs(l["Close"] - l["EMA20"]) / l["EMA20"]

                # relaxed filter (IMPORTANT)
                if dist < 0.015:

                    signal = None

                    if l["Close"] > l["EMA20"] and l["Close"] > l["VWAP"]:
                        signal = "BUY 🟢"
                    elif l["Close"] < l["EMA20"] and l["Close"] < l["VWAP"]:
                        signal = "SELL 🔴"

                    if signal:

                        big_score = (
                            (l["VolSpike"] > 1.5) * 40 +
                            (l["VolSpike"] > 2.0) * 30 +
                            (abs(l["Close"] - l["Open"]) > l["ATR"]) * 30
                        )

                        results.append({
                            "TIME": df.index[-1].astimezone(IST).strftime("%H:%M"),
                            "STOCK": s,
                            "SIGNAL": signal,
                            "ENTRY": round(l["Close"], 2),
                            "BIG PLAYER SCORE": f"{big_score}/100",
                            "SL": round(l["Close"] - l["ATR"]*1.5 if "BUY" in signal else l["Close"] + l["ATR"]*1.5, 2),
                            "TARGET": round(l["Close"] + l["ATR"]*3 if "BUY" in signal else l["Close"] - l["ATR"]*3, 2)
                        })

            except:
                continue

        if results:
            df_live = pd.DataFrame(results)

            st.success(f"🔥 SIGNALS FOUND: {len(df_live)}")
            st.dataframe(df_live, use_container_width=True)

            st.download_button(
                "📥 DOWNLOAD LIVE EXCEL",
                data=to_excel(df_live),
                file_name=f"LIVE_{now.strftime('%Y%m%d_%H%M')}.xlsx"
            )
        else:
            st.warning("No signals right now")

# =============================
# BACKTEST
# =============================
with tab2:
    bt_date = st.date_input("Select Date", value=now.date() - timedelta(days=1))

    if st.button("RUN BACKTEST"):
        logs = []

        for s in stocks:
            try:
                df = data.get(s + ".NS")
                if df is None or df.empty:
                    continue

                df = add_indicators(df.dropna())
                df.index = pd.to_datetime(df.index)
                df["DATE"] = df.index.date

                df_day = df[df["DATE"] == bt_date]
                if df_day.empty:
                    continue

                for i in range(20, len(df_day)):
                    r = df_day.iloc[i]

                    dist = abs(r["Close"] - r["EMA20"]) / r["EMA20"]

                    if dist < 0.015:

                        if r["Close"] > r["EMA20"] and r["Close"] > r["VWAP"]:
                            sig = "BUY"
                        elif r["Close"] < r["EMA20"] and r["Close"] < r["VWAP"]:
                            sig = "SELL"
                        else:
                            sig = None

                        if sig:
                            logs.append({
                                "TIME": df_day.index[i].strftime("%H:%M"),
                                "STOCK": s,
                                "TYPE": sig,
                                "ENTRY": round(r["Close"], 2),
                                "SL": round(r["Close"] - r["ATR"]*1.5 if sig=="BUY" else r["Close"] + r["ATR"]*1.5, 2),
                                "TARGET": round(r["Close"] + r["ATR"]*3 if sig=="BUY" else r["Close"] - r["ATR"]*3, 2),
                                "VOLUME": r["Volume"]
                            })

            except:
                continue

        if logs:
            df_bt = pd.DataFrame(logs)

            st.success(f"🔥 BACKTEST SIGNALS: {len(df_bt)}")
            st.dataframe(df_bt, use_container_width=True)

            st.download_button(
                "📥 DOWNLOAD BACKTEST EXCEL",
                data=to_excel(df_bt),
                file_name=f"BACKTEST_{bt_date}.xlsx"
            )
        else:
            st.error("No backtest data found")
