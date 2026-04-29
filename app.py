import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta, time
import pytz
import io

# ==========================================
# CONFIG
# ==========================================
st.set_page_config(page_title="🚀 NSE AI PRO V63", layout="wide")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V63 - HIGH PROBABILITY ENGINE")
st.write(f"🕒 {now.strftime('%Y-%m-%d %H:%M:%S')}")

# ==========================================
# NSE STOCKS
# ==========================================
nse_200 = [
"RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","ITC","LT","AXISBANK","KOTAKBANK",
"BHARTIARTL","HINDUNILVR","BAJFINANCE","ASIANPAINT","MARUTI","TITAN","HCLTECH","SUNPHARMA",
"ULTRACEMCO","NTPC","JSWSTEEL","POWERGRID","M&M","ONGC","HINDALCO","TATAMOTORS","ADANIPORTS",
"COALINDIA","GRASIM","BAJAJFINSV","BRITANNIA","EICHERMOT","DIVISLAB","CIPLA","TECHM",
"NESTLEIND","BPCL","INDUSINDBK","HDFCLIFE","APOLLOHOSP","DRREDDY","BAJAJ-AUTO","SBILIFE",
"HEROMOTOCO","UPL","TATACONSUM","SHREECEM","IRCTC","HAL","BEL","DLF","GAIL","IOC"
]

tickers = [s + ".NS" for s in nse_200]

# ==========================================
# DATA FETCH
# ==========================================
@st.cache_data(ttl=300)
def get_data():
    return yf.download(tickers, period="7d", interval="5m", group_by="ticker", threads=True)

# ==========================================
# INDICATORS
# ==========================================
def indicators(df):
    df = df.copy()
    df["EMA20"] = df["Close"].ewm(span=20, min_periods=20).mean()
    df["SUPPORT"] = df["Low"].rolling(20, min_periods=20).min()
    df["RESISTANCE"] = df["High"].rolling(20, min_periods=20).max()
    df["VOLAVG"] = df["Volume"].rolling(20, min_periods=20).mean()
    return df

# ==========================================
# LOGIC
# ==========================================
def big_player(row):
    return row["Volume"] > (row["VOLAVG"] * 1.5) if pd.notna(row["VOLAVG"]) else False

def session_check(ts):
    t = ts.time()
    return time(9,15) <= t <= time(15,30)

# -------- PULLBACK SIGNAL --------
def pullback_signal(row, prev):
    if pd.isna(row["EMA20"]): return None, None, None, None

    # BUY PULLBACK
    if (
        row["Close"] > row["EMA20"] and
        prev["Close"] > prev["EMA20"] and
        row["Low"] <= row["EMA20"] * 1.002 and
        row["Close"] > row["EMA20"]
    ):
        entry = row["Close"]
        sl = row["EMA20"] * 0.995
        return "PULLBACK BUY", entry, sl, entry + (entry - sl) * 2

    # SELL PULLBACK
    if (
        row["Close"] < row["EMA20"] and
        prev["Close"] < prev["EMA20"] and
        row["High"] >= row["EMA20"] * 0.998 and
        row["Close"] < row["EMA20"]
    ):
        entry = row["Close"]
        sl = row["EMA20"] * 1.005
        return "PULLBACK SELL", entry, sl, entry - (sl - entry) * 2

    return None, None, None, None

# -------- MAIN SIGNAL ENGINE --------
def signal_engine(row, prev):

    if pd.isna(row["EMA20"]) or pd.isna(row["SUPPORT"]):
        return None, None, None, None

    # 🔥 PRIORITY: PULLBACK
    sig, entry, sl, target = pullback_signal(row, prev)
    if sig:
        return sig, entry, sl, target

    entry = row["Close"]

    # BUY SUPPORT
    if entry <= row["SUPPORT"] * 1.002:
        sl = row["SUPPORT"] * 0.995
        return "BUY SUPPORT", entry, sl, entry + (entry - sl) * 2

    # SELL RESISTANCE
    if entry >= row["RESISTANCE"] * 0.998:
        sl = row["RESISTANCE"] * 1.002
        return "SELL RESISTANCE", entry, sl, entry - (sl - entry) * 2

    # EMA BUY
    if prev["Close"] < prev["EMA20"] and entry > row["EMA20"]:
        sl = row["EMA20"] * 0.995
        return "EMA BUY", entry, sl, entry + (entry - sl) * 2

    # EMA SELL
    if prev["Close"] > prev["EMA20"] and entry < row["EMA20"]:
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

                if len(df) < 30:
                    continue

                df = indicators(df)

                row = df.iloc[-1]
                prev = df.iloc[-2]
                ts = df.index[-1].tz_convert(IST)

                if not session_check(ts):
                    continue

                # 🔥 HIGH PROBABILITY FILTER
                if row["Volume"] < row["VOLAVG"] * 1.5:
                    continue

                if abs(row["Close"] - row["EMA20"]) / row["EMA20"] > 0.01:
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
                        "BIG PLAYER": "🔥 YES" if big_player(row) else "NO",
                        "PULLBACK": "YES" if "PULLBACK" in sig else "NO"
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
                df.index = pd.to_datetime(df.index).tz_convert(IST)

                df = df[df.index.date == pd.Timestamp(test_date).date()]

                if len(df) < 30:
                    continue

                df = indicators(df)

                for i in range(1, len(df)):
                    row = df.iloc[i]
                    prev = df.iloc[i-1]
                    ts = df.index[i]

                    if not session_check(ts):
                        continue

                    # FILTER
                    if row["Volume"] < row["VOLAVG"] * 1.5:
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
                            "BIG PLAYER": "🔥 YES" if big_player(row) else "NO",
                            "PULLBACK": "YES" if "PULLBACK" in sig else "NO"
                        })

            except:
                continue

        df_out = pd.DataFrame(logs)

        if not df_out.empty:
            st.success(f"Total Signals: {len(df_out)}")
            st.dataframe(df_out, use_container_width=True)

            # EXCEL EXPORT PRO
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                df_out.to_excel(writer, index=False, sheet_name="SIGNALS")

                workbook = writer.book
                worksheet = writer.sheets["SIGNALS"]
                header_format = workbook.add_format({'bold': True})
                worksheet.set_row(0, None, header_format)

            buffer.seek(0)

            st.download_button(
                "⬇️ Download Excel",
                data=buffer,
                file_name="NSE_AI_V63.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("No signals found.")
