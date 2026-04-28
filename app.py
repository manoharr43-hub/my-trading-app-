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
st.set_page_config(page_title="🚀 NSE AI PRO V44", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V44 - NSE 200 MASTER PULLBACK")
st.write(f"🕒 Market Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")

# =============================
# STOCK LIST (NSE 200)
# =============================
stocks = [
    "ABB","ACC","ADANIENT","ADANIPORTS","ADANIPOWER","ATGL","AWL","ABCAPITAL","ABFRL",
    "ALKEM","AMBUJACEM","APOLLOHOSP","APOLLOTYRE","ASHOKLEY","ASIANPAINT","ASTRAL","AUBANK",
    "AUROPHARMA","AXISBANK","BAJAJ-AUTO","BAJFINANCE","BAJAJFINSV","BAJAJHLDNG",
    "BANDHANBNK","BANKBARODA","BEL","BERGEPAINT","BHARTIARTL","BIOCON","BPCL",
    "BRITANNIA","CANBK","CIPLA","COALINDIA","CONCOR","CUMMINSIND","DLF","DABUR",
    "DIVISLAB","DRREDDY","EICHERMOT","ESCORTS","FEDERALBNK","GAIL","GLENMARK",
    "GODREJCP","GRASIM","HAL","HAVELLS","HCLTECH","HDFCBANK","HDFCLIFE",
    "HEROMOTOCO","HINDALCO","HINDUNILVR","ICICIBANK","ICICIGI","ICICIPRULI",
    "IDFCFIRSTB","INDIGO","INDUSINDBK","INFY","IOC","IRCTC","ITC","JINDALSTEL",
    "JSWSTEEL","JUBLFOOD","KOTAKBANK","LT","LTIM","LUPIN","M&M","MARUTI",
    "NESTLEIND","NTPC","ONGC","PIDILITIND","PNB","POWERGRID","RELIANCE",
    "SBIN","SUNPHARMA","TATAMOTORS","TATASTEEL","TCS","TECHM","TITAN","ULTRACEMCO","WIPRO"
]

# =============================
# INDICATORS
# =============================
def add_indicators(df):
    df = df.copy()
    if len(df) < 20:
        return df

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

@st.cache_data(ttl=60)
def fetch_data(symbols):
    tickers = [s + ".NS" for s in symbols]
    return yf.download(tickers, period="5d", interval="5m", group_by="ticker", progress=False)

data = fetch_data(stocks)

# =============================
# EXCEL EXPORT
# =============================
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="REPORT")
    return output.getvalue()

# =============================
# TABS
# =============================
tab1, tab2 = st.tabs(["🔍 LIVE SCAN", "📊 BACKTEST"])

# =============================
# TAB 1 - LIVE SCAN
# =============================
with tab1:
    if st.button("RUN LIVE SCAN"):
        results = []

        for s in stocks:
            try:
                df_raw = data.get(s + ".NS")
                if df_raw is None or df_raw.empty:
                    continue

                df = add_indicators(df_raw.dropna())
                l = df.iloc[-1]

                dist = abs(l["Close"] - l["EMA20"]) / l["EMA20"]

                if dist < 0.004:
                    signal = None

                    if l["Close"] > l["VWAP"] and l["Close"] > l["Open"]:
                        signal = "BUY 🟢"
                    elif l["Close"] < l["VWAP"] and l["Close"] < l["Open"]:
                        signal = "SELL 🔴"

                    if signal:
                        entry = round(l["Close"], 2)

                        results.append({
                            "TIME": df.index[-1].astimezone(IST).strftime("%H:%M"),
                            "STOCK": s,
                            "SIGNAL": signal,
                            "ENTRY": entry,
                            "BIG PLAYER": "🔥 YES" if l["Volume"] > l["VolAvg"]*2.5 else "-",
                            "SL": round(entry - l["ATR"]*1.5 if "BUY" in signal else entry + l["ATR"]*1.5, 2),
                            "TARGET": round(entry + l["ATR"]*3 if "BUY" in signal else entry - l["ATR"]*3, 2)
                        })

            except:
                continue

        if results:
            df_live = pd.DataFrame(results)

            st.success(f"Signals Found: {len(df_live)}")
            st.dataframe(df_live, use_container_width=True)

            # ✅ LIVE EXCEL DOWNLOAD FIX
            st.download_button(
                "📥 DOWNLOAD LIVE EXCEL",
                data=to_excel(df_live),
                file_name=f"LIVE_SCAN_{now.strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("No signals found")

# =============================
# TAB 2 - BACKTEST
# =============================
with tab2:
    bt_date = st.date_input("Select Date", value=now.date() - timedelta(days=1))

    if st.button("RUN BACKTEST"):
        logs = []

        for s in stocks:
            try:
                df_raw = data.get(s + ".NS")
                if df_raw is None:
                    continue

                df = add_indicators(df_raw.dropna())
                df.index = df.index.tz_convert(IST)

                df_day = df[df.index.date == bt_date]
                if df_day.empty:
                    continue

                for i in range(20, len(df_day)):
                    r = df_day.iloc[i]
                    dist = abs(r["Close"] - r["EMA20"]) / r["EMA20"]

                    if dist < 0.004:
                        sig = None

                        if r["Close"] > r["VWAP"] and r["Close"] > r["Open"]:
                            sig = "BUY"
                        elif r["Close"] < r["VWAP"] and r["Close"] < r["Open"]:
                            sig = "SELL"

                        if sig:
                            entry = round(r["Close"], 2)

                            logs.append({
                                "TIME": df_day.index[i].strftime("%H:%M"),
                                "STOCK": s,
                                "TYPE": sig,
                                "ENTRY": entry,
                                "SL": round(entry - r["ATR"]*1.5 if sig=="BUY" else entry + r["ATR"]*1.5, 2),
                                "TARGET": round(entry + r["ATR"]*3 if sig=="BUY" else entry - r["ATR"]*3, 2),
                                "BIG PLAYER": "🔥" if r["Volume"] > r["VolAvg"]*2.5 else "-"
                            })

            except:
                continue

        if logs:
            df_bt = pd.DataFrame(logs)
            st.dataframe(df_bt, use_container_width=True)

            st.download_button(
                "📥 DOWNLOAD BACKTEST EXCEL",
                data=to_excel(df_bt),
                file_name=f"BACKTEST_{bt_date}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("No backtest signals found")
