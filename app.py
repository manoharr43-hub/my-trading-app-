import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta, time
import pytz
import io

# ==========================================
# CONFIG
# ==========================================
st.set_page_config(page_title="🚀 NSE AI PRO V66", layout="wide")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V66 - FULL AI SYSTEM")
st.write(f"🕒 {now.strftime('%Y-%m-%d %H:%M:%S')}")

# ==========================================
# SESSION STORAGE
# ==========================================
if "live_logs" not in st.session_state:
    st.session_state.live_logs = []

# ==========================================
# STOCK LIST
# ==========================================
nse_200 = ["RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","ITC","LT","AXISBANK","KOTAKBANK"]

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
    df["EMA20"] = df["Close"].ewm(span=20, min_periods=20).mean()
    df["SUPPORT"] = df["Low"].rolling(20, min_periods=20).min()
    df["RESISTANCE"] = df["High"].rolling(20, min_periods=20).max()
    df["VOLAVG"] = df["Volume"].rolling(20, min_periods=20).mean()
    return df

# ==========================================
# LOGIC
# ==========================================
def big_player(row):
    return row["Volume"] > row["VOLAVG"] * 1.5 if pd.notna(row["VOLAVG"]) else False

def pullback_signal(row, prev):
    if pd.isna(row["EMA20"]):
        return None, None, None, None

    if row["Close"] > row["EMA20"] and row["Low"] <= row["EMA20"] * 1.002:
        entry = row["Close"]
        sl = row["EMA20"] * 0.995
        return "BUY", entry, sl, entry + (entry - sl) * 2

    if row["Close"] < row["EMA20"] and row["High"] >= row["EMA20"] * 0.998:
        entry = row["Close"]
        sl = row["EMA20"] * 1.005
        return "SELL", entry, sl, entry - (sl - entry) * 2

    return None, None, None, None

def signal_engine(row, prev):
    if pd.isna(row["EMA20"]):
        return None, None, None, None, None

    sig, entry, sl, target = pullback_signal(row, prev)
    if sig:
        return sig, entry, sl, target, "PULLBACK"

    entry = row["Close"]

    if entry <= row["SUPPORT"] * 1.002:
        sl = row["SUPPORT"] * 0.995
        return "BUY", entry, sl, entry + (entry - sl) * 2, "SUPPORT"

    if entry >= row["RESISTANCE"] * 0.998:
        sl = row["RESISTANCE"] * 1.002
        return "SELL", entry, sl, entry - (sl - entry) * 2, "RESISTANCE"

    if prev["Close"] < prev["EMA20"] and entry > row["EMA20"]:
        sl = row["EMA20"] * 0.995
        return "BUY", entry, sl, entry + (entry - sl) * 2, "EMA"

    if prev["Close"] > prev["EMA20"] and entry < row["EMA20"]:
        sl = row["EMA20"] * 1.005
        return "SELL", entry, sl, entry - (sl - entry) * 2, "EMA"

    return None, None, None, None, None

def ai_score(row, prev):
    score = 0

    if row["Close"] > row["EMA20"]:
        score += 2

    if big_player(row):
        score += 2

    if abs(row["Close"] - row["SUPPORT"]) < row["Close"] * 0.003:
        score += 2

    if pullback_signal(row, prev)[0]:
        score += 3

    return score

def session_check(ts):
    return time(9,15) <= ts.time() <= time(15,30)

# ==========================================
# UI
# ==========================================
if st.button("🚀 RUN LIVE SCAN"):
    data = get_data()

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

            score = ai_score(row, prev)
            sig, entry, sl, target, typ = signal_engine(row, prev)

            if sig and score >= 7:
                record = {
                    "TIME": ts.strftime("%H:%M"),
                    "STOCK": s,
                    "SIGNAL": sig,
                    "ENTRY": round(entry,2),
                    "SL": round(sl,2),
                    "TARGET": round(target,2),
                    "SCORE": score,
                    "BIG PLAYER ENTRY": "YES" if big_player(row) else "NO",
                    "PULLBACK": "YES" if typ == "PULLBACK" else "NO",
                    "TYPE": typ
                }

                st.session_state.live_logs.append(record)

        except:
            continue

# ==========================================
# DISPLAY DATA
# ==========================================
st.subheader("📊 FULL DAY SIGNALS")

df_live = pd.DataFrame(st.session_state.live_logs)

if not df_live.empty:
    st.dataframe(df_live, use_container_width=True)

# ==========================================
# EXCEL DOWNLOAD
# ==========================================
if not df_live.empty:
    buffer = io.BytesIO()

    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df_live.to_excel(writer, index=False, sheet_name="SIGNALS")

        workbook = writer.book
        worksheet = writer.sheets["SIGNALS"]

        header_format = workbook.add_format({'bold': True})
        worksheet.set_row(0, None, header_format)

        for i, col in enumerate(df_live.columns):
            width = max(df_live[col].astype(str).map(len).max(), len(col))
            worksheet.set_column(i, i, width + 2)

    buffer.seek(0)

    st.download_button(
        "⬇️ Download Excel",
        data=buffer,
        file_name=f"NSE_AI_V66_{now.strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ==========================================
# RESET
# ==========================================
if st.button("🔄 RESET DATA"):
    st.session_state.live_logs = []
