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
st.set_page_config(page_title="🚀 NSE AI PRO V45.4", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V45.4 - LIVE + BACKTEST + SECTOR + BIG MOVE")
st.write(f"🕒 Market Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")

# =============================
# STOCKS
# =============================
stocks = [
    "RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","AXISBANK","KOTAKBANK",
    "LT","ITC","HINDUNILVR","ASIANPAINT","MARUTI","SUNPHARMA","ONGC","NTPC",
    "TATASTEEL","JSWSTEEL","BAJFINANCE","BAJAJFINSV","ADANIENT","ADANIPORTS",
    "ULTRACEMCO","GRASIM","TECHM","WIPRO","HCLTECH","NESTLEIND","CIPLA",
    "DIVISLAB","DRREDDY","TITAN","M&M","HEROMOTOCO","EICHERMOT","COALINDIA",
    "SHREECEM","HAVELLS","SIEMENS","PIDILITIND","BEL","DLF","INDUSINDBK",
    "PNB","BANKBARODA","CANBK","FEDERALBNK","IDFCFIRSTB","YESBANK","ZEEL","ZOMATO"
]

# =============================
# SECTOR MAP
# =============================
sector_map = {
    "RELIANCE":"ENERGY","ONGC":"ENERGY","IOC":"ENERGY",
    "TCS":"IT","INFY":"IT","WIPRO":"IT","TECHM":"IT","HCLTECH":"IT",
    "HDFCBANK":"BANK","ICICIBANK":"BANK","SBIN":"BANK","AXISBANK":"BANK","KOTAKBANK":"BANK",
    "BAJFINANCE":"FINANCE","BAJAJFINSV":"FINANCE",
    "TATASTEEL":"METAL","JSWSTEEL":"METAL",
    "HINDUNILVR":"FMCG","ITC":"FMCG","NESTLEIND":"FMCG"
}

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
    df["BigMove"] = abs(df["Close"] - df["Open"]) / (df["ATR"] + 1e-9)
    return df

# =============================
# DATA
# =============================
@st.cache_data(ttl=60)
def load_data():
    return yf.download([s+".NS" for s in stocks], period="5d", interval="5m", group_by="ticker")

data = load_data()

# =============================
# EXCEL
# =============================
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

# =============================
# TABS
# =============================
tab1, tab2, tab3 = st.tabs(["🔍 LIVE SCAN", "📊 BACKTEST", "🔥 BIG MOVE"])

# =============================
# LIVE SCAN
# =============================
with tab1:
    if st.button("RUN LIVE SCAN", key="live_btn"):
        results, sector_summary = [], {}
        for s in stocks:
            try:
                df = data.get(s+".NS")
                if df is None or df.empty: continue
                df = add_indicators(df.dropna())
                l = df.iloc[-1]
                dist = abs(l["Close"] - l["EMA20"]) / l["EMA20"]

                if dist < 0.015:
                    signal = None
                    if l["Close"] > l["EMA20"] and l["Close"] > l["VWAP"]:
                        signal = "BUY 🟢"
                    elif l["Close"] < l["EMA20"] and l["Close"] < l["VWAP"]:
                        signal = "SELL 🔴"

                    if signal:
                        sector = sector_map.get(s, "OTHER")
                        sector_summary[sector] = sector_summary.get(sector, 0) + 1
                        results.append({
                            "TIME": df.index[-1].astimezone(IST).strftime("%H:%M"),
                            "STOCK": s,
                            "SECTOR": sector,
                            "SIGNAL": signal,
                            "ENTRY": round(l["Close"],2),
                            "BIG MOVE": "🔥" if l["BigMove"] > 1 else "-",
                            "BIG PLAYER": "🔥" if l["VolSpike"] > 1.5 else "-",
                            "SL": round(l["Close"] - l["ATR"]*1.5 if "BUY" in signal else l["Close"] + l["ATR"]*1.5,2),
                            "TARGET": round(l["Close"] + l["ATR"]*3 if "BUY" in signal else l["Close"] - l["ATR"]*3,2)
                        })
            except Exception:
                continue

        if results:
            df_live = pd.DataFrame(results)
            st.success(f"🔥 SIGNALS: {len(df_live)}")
            st.dataframe(df_live, use_container_width=True)
            st.subheader("📊 Sector Summary")
            st.write(pd.DataFrame(list(sector_summary.items()), columns=["SECTOR","COUNT"]))
            st.download_button("📥 LIVE EXCEL", to_excel(df_live),
                               file_name=f"LIVE_{now.strftime('%Y%m%d_%H%M')}.xlsx")
        else:
            st.warning("No signals found")

# =============================
# BACKTEST
# =============================
with tab2:
    bt_date = st.date_input("Select Date", value=now.date()-timedelta(days=1))
    if st.button("RUN BACKTEST", key="bt_btn"):
        logs = []
        for s in stocks:
            try:
                df = data.get(s+".NS")
                if df is None: continue
                df = add_indicators(df.dropna())
                df.index = pd.to_datetime(df.index)
                df["DATE"] = df.index.date
                df_day = df[df["DATE"] == bt_date]
                if df_day.empty: continue

                for i in range(20, len(df_day)):
                    r = df_day.iloc[i]
                    dist = abs(r["Close"] - r["EMA20"]) / r["EMA20"]
                    if dist < 0.015:
                        sig = "BUY" if r["Close"] > r["EMA20"] and r["Close"] > r["VWAP"] else "SELL" if r["Close"] < r["EMA20"] and r["Close"] < r["VWAP"] else None
                        if sig:
                            logs.append({
                                "TIME": df_day.index[i].strftime("%H:%M"),
                                "STOCK": s,
                                "TYPE": sig,
                                "ENTRY": round(r["Close"],2),
                                "BIG MOVE": "🔥" if r["BigMove"]>1 else "-",
                                "VOLUME": r["Volume"]
                            })
            except Exception:
                continue

        if logs:
            df_bt = pd.DataFrame(logs)
            st.success(f"🔥 BACKTEST SIGNALS: {len(df_bt)}")
            st.dataframe(df_bt, use_container_width=True)
            st.download_button("📥 BACKTEST EXCEL", to_excel(df_bt),
                               file_name=f"BACKTEST_{bt_date}.xlsx")
        else:
            st.error("No backtest data found")

# =============================
# BIG MOVE TAB
# =============================
with tab3:
    if st.button("RUN BIG MOVE SCAN", key="bm_btn"):
        big_logs = []
        for s in stocks:
            try:
                df = data.get(s+".NS")
                if df is None or df.empty: continue
                df = add_indicators(df.dropna())
                l = df.iloc[-1]
                if l["BigMove"] > 1 or l["VolSpike"] > 1.
