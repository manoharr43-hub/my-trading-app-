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
st.set_page_config(page_title="🚀 NSE AI PRO V45 LIVE", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V45 - BIG PLAYER LIVE SCANNER")
st.write(f"🕒 Market Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")

# =============================
# STOCK LIST (SHORT FOR SPEED)
# =============================
stocks = [
    "RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","LT","ITC",
    "AXISBANK","KOTAKBANK","HINDUNILVR","BHARTIARTL","TATAMOTORS",
    "BAJFINANCE","MARUTI","SUNPHARMA","WIPRO","ONGC","NTPC","POWERGRID"
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

    # 🔥 BIG PLAYER SMART FLOW (NEW)
    df["VolumeSpike"] = df["Volume"] / (df["VolAvg"] + 1e-9)
    df["PriceMove"] = abs(df["Close"] - df["Open"])

    return df

# =============================
# DATA FETCH
# =============================
@st.cache_data(ttl=60)
def fetch():
    tickers = [s + ".NS" for s in stocks]
    return yf.download(tickers, period="5d", interval="5m", group_by="ticker", progress=False)

data = fetch()

# =============================
# EXCEL EXPORT
# =============================
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="LIVE_SCAN")
    return output.getvalue()

# =============================
# LIVE SCANNER
# =============================
if st.button("🔥 RUN LIVE BIG PLAYER SCAN"):
    results = []

    for s in stocks:
        try:
            df_raw = data.get(s + ".NS")
            if df_raw is None or df_raw.empty:
                continue

            df = add_indicators(df_raw.dropna())
            l = df.iloc[-1]

            dist = abs(l["Close"] - l["EMA20"]) / l["EMA20"]

            # 🔥 LOOSER RANGE (IMPORTANT FIX)
            if dist < 0.015:

                signal = None

                # BUY / SELL LOGIC
                if l["Close"] > l["EMA20"] and l["Close"] > l["VWAP"]:
                    signal = "BUY 🟢 PULLBACK"
                elif l["Close"] < l["EMA20"] and l["Close"] < l["VWAP"]:
                    signal = "SELL 🔴 PULLBACK"

                if signal:

                    # 🔥 BIG PLAYER LOGIC (STRONG UPGRADE)
                    big_player_score = (
                        (l["VolumeSpike"] > 1.5) * 40 +
                        (l["PriceMove"] > l["ATR"]) * 30 +
                        (l["VolumeSpike"] > 2.0) * 30
                    )

                    results.append({
                        "TIME": df.index[-1].astimezone(IST).strftime("%H:%M"),
                        "STOCK": s,
                        "SIGNAL": signal,
                        "ENTRY": round(l["Close"], 2),
                        "BIG PLAYER SCORE": f"{big_player_score}/100",
                        "VOLUME SPIKE": round(l["VolumeSpike"], 2),
                        "SL": round(l["Close"] - l["ATR"]*1.5 if "BUY" in signal else l["Close"] + l["ATR"]*1.5, 2),
                        "TARGET": round(l["Close"] + l["ATR"]*3 if "BUY" in signal else l["Close"] - l["ATR"]*3, 2)
                    })

        except:
            continue

    if results:
        df_live = pd.DataFrame(results)

        st.success(f"🔥 BIG PLAYER SIGNALS: {len(df_live)}")
        st.dataframe(df_live, use_container_width=True)

        st.download_button(
            "📥 DOWNLOAD LIVE EXCEL",
            data=to_excel(df_live),
            file_name=f"BIG_PLAYER_LIVE_{now.strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("No BIG PLAYER activity detected right now.")
