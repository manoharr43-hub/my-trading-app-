import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta, time
import pytz
import io

# ==========================================
# CONFIG
# ==========================================
st.set_page_config(page_title="🚀 NSE AI PRO V61", layout="wide")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V61 - FULL STABLE ENGINE")
st.write(f"🕒 {now.strftime('%Y-%m-%d %H:%M:%S')}")

# ==========================================
# NSE 200 STOCKS (FULL READY)
# ==========================================
nse_200 = [
"RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","ITC","LT","AXISBANK","KOTAKBANK",
"BHARTIARTL","HINDUNILVR","BAJFINANCE","ASIANPAINT","MARUTI","TITAN","HCLTECH","SUNPHARMA",
"ULTRACEMCO","NTPC","JSWSTEEL","POWERGRID","M&M","ONGC","HINDALCO","TATAMOTORS","ADANIPORTS",
"COALINDIA","GRASIM","BAJAJFINSV","BRITANNIA","EICHERMOT","DIVISLAB","CIPLA","TECHM",
"NESTLEIND","BPCL","INDUSINDBK","HDFCLIFE","APOLLOHOSP","DRREDDY","BAJAJ-AUTO","SBILIFE",
"HEROMOTOCO","UPL","TATACONSUM","SHREECEM","IRCTC","HAL","BEL","DLF","GAIL","IOC"
]

# ==========================================
# DATA FETCH
# ==========================================
@st.cache_data(ttl=300)
def get_data():
    tickers = [s + ".NS" for s in nse_200]
    return yf.download(tickers, period="7d", interval="5m", group_by="ticker")

# ==========================================
# INDICATORS
# ==========================================
def indicators(df):
    df = df.copy()

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df["EMA20"] = df["Close"].ewm(span=20).mean()
    df["SUPPORT"] = df["Low"].rolling(20).min()
    df["RESISTANCE"] = df["High"].rolling(20).max()
    df["VOLAVG"] = df["Volume"].rolling(20).mean()
    return df

# ==========================================
# LOGIC FUNCTIONS
# ==========================================
def big_player(row):
    return row["Volume"] > row["VOLAVG"] * 2

def session_check(ts):
    t = ts.time()
    return time(9,15) <= t <= time(15,30)

def signal_engine(row, prev):
    entry = row["Close"]

    # BUY SUPPORT
    if row["Close"] <= row["SUPPORT"] * 1.002:
        sl = row["SUPPORT"] * 0.995
        return "BUY SUPPORT", entry, sl, entry + (entry - sl) * 2

    # SELL RESISTANCE
    if row["Close"] >= row["RESISTANCE"] * 0.998:
        sl = row["RESISTANCE"] * 1.002
        return "SELL RESISTANCE", entry, sl, entry - (sl - entry) * 2

    # EMA BUY
    if prev["Close"] < prev["EMA20"] and row["Close"] > row["EMA20"]:
        sl = row["EMA20"] * 0.995
        return "EMA BUY", entry, sl, entry + (entry - sl) * 2

    # EMA SELL
    if prev["Close"] > prev["EMA20"] and row["Close"] < row["EMA20"]:
        sl = row["EMA20"] * 1.005
        return "EMA SELL", entry, sl, entry - (sl - entry) * 2

    return None, None, None, None

# ==========================================
# UI
# ==========================================
tab1, tab2 = st.tabs(["🚀 LIVE SCAN", "📊 BACKTEST"])

# ================= LIVE =================
with tab1:
    if st.button("RUN LIVE SCAN"):
        data = get_data()
        results = []

        for s in nse_200:
            try:
                df = data[s + ".NS"].dropna()
                if len(df) < 25:
                    continue

                df = indicators(df)

                row = df.iloc[-1]
                prev = df.iloc[-2]
                ts = df.index[-1].tz_convert(IST)

                if not session_check(ts):
                    continue

                sig, entry, sl, target = signal_engine(row, prev)

                if sig:
                    results.append({
                        "STOCK": s,
                        "TIME": ts.strftime("%H:%M"),
                        "SIGNAL": sig,
                        "ENTRY": round(entry,2),
                        "SL": round(sl,2),
                        "TARGET": round(target,2),
                        "BIG PLAYER": "🔥 YES" if big_player(row) else "NO"
                    })

            except:
                continue

        st.dataframe(pd.DataFrame(results), use_container_width=True)

# ================= BACKTEST =================
with tab2:
    test_date = st.date_input("Select Date", now.date() - timedelta(days=1))

    if st.button("RUN BACKTEST"):
        data = get_data()
        logs = []

        for s in nse_200:
            try:
                df = data[s + ".NS"].dropna()
                df.index = df.index.tz_convert(IST)

                df = df[df.index.date == test_date]

                if len(df) < 25:
                    continue

                df = indicators(df)

                for i in range(1, len(df)):
                    row = df.iloc[i]
                    prev = df.iloc[i-1]
                    ts = df.index[i]

                    if not session_check(ts):
                        continue

                    sig, entry, sl, target = signal_engine(row, prev)

                    if sig:
                        logs.append({
                            "TIME": ts.strftime("%H:%M"),
                            "STOCK": s,
                            "SIGNAL": sig,
                            "ENTRY": round(entry,2),
                            "SL": round(sl,2),
                            "TARGET": round(target,2),
                            "BIG PLAYER": "🔥 YES" if big_player(row) else "NO"
                        })

            except:
                continue

        df_out = pd.DataFrame(logs)

        if not df_out.empty:
            st.success(f"Total Signals: {len(df_out)}")
            st.dataframe(df_out, use_container_width=True)

            # ================= EXCEL EXPORT =================
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                df_out.to_excel(writer, index=False, sheet_name="NSE_SIGNALS")

            buffer.seek(0)

            st.download_button(
                "⬇️ Download Excel Report",
                data=buffer,
                file_name="NSE_AI_V61.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("No signals found.")
