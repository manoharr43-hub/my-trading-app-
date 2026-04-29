import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta, time
import pytz
import io

# ==========================================
# CONFIG
# ==========================================
st.set_page_config(page_title="🚀 NSE AI PRO V67", layout="wide")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V67 - FULL SYSTEM")
st.write(f"🕒 {now.strftime('%Y-%m-%d %H:%M:%S')}")

# ==========================================
# SESSION
# ==========================================
if "live_logs" not in st.session_state:
    st.session_state.live_logs = []

# ==========================================
# NSE 200 STOCKS
# ==========================================
nse_200 = [
"RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","ITC","LT","AXISBANK","KOTAKBANK",
"BHARTIARTL","HINDUNILVR","BAJFINANCE","ASIANPAINT","MARUTI","TITAN","HCLTECH","SUNPHARMA",
"ULTRACEMCO","NTPC","JSWSTEEL","POWERGRID","M&M","ONGC","HINDALCO","TATAMOTORS","ADANIPORTS",
"COALINDIA","GRASIM","BAJAJFINSV","BRITANNIA","EICHERMOT","DIVISLAB","CIPLA","TECHM",
"NESTLEIND","BPCL","INDUSINDBK","HDFCLIFE","APOLLOHOSP","DRREDDY","BAJAJ-AUTO","SBILIFE",
"HEROMOTOCO","UPL","TATACONSUM","SHREECEM","IRCTC","HAL","BEL","DLF","GAIL","IOC",
"PNB","BANKBARODA","CANBK","IDFCFIRSTB","FEDERALBNK","RBLBANK","AUBANK","BANDHANBNK",
"ESCORTS","ASHOKLEY","TVSMOTOR","MUTHOOTFIN","PEL","SRF","PIIND","NAUKRI","ZOMATO",
"PAYTM","POLYCAB","DABUR","MARICO","COLPAL","GODREJCP","ADANIENT","ADANIGREEN",
"AMBUJACEM","ACC","SIEMENS","ABB","HAVELLS","VEDL","NMDC","SAIL","PAGEIND","TRENT",
"DMART","VBL","ICICIGI","HDFCAMC","SBICARD","LUPIN","ALKEM","BIOCON","INDIGO",
"CONCOR","MPHASIS","LTIM","PERSISTENT","COFORGE","RECLTD","PFC","IRFC"
]

tickers = [s + ".NS" for s in nse_200]

# ==========================================
# DATA
# ==========================================
@st.cache_data(ttl=300)
def get_data():
    return yf.download(tickers, period="7d", interval="5m", group_by="ticker")

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
    if pd.isna(row["EMA20"]): return None, None, None, None

    if row["Close"] > row["EMA20"] and row["Low"] <= row["EMA20"]*1.002:
        entry = row["Close"]
        sl = row["EMA20"]*0.995
        return "BUY", entry, sl, entry + (entry - sl)*2

    if row["Close"] < row["EMA20"] and row["High"] >= row["EMA20"]*0.998:
        entry = row["Close"]
        sl = row["EMA20"]*1.005
        return "SELL", entry, sl, entry - (sl - entry)*2

    return None, None, None, None

def signal_engine(row, prev):
    if pd.isna(row["EMA20"]): return None, None, None, None, None

    sig, entry, sl, target = pullback_signal(row, prev)
    if sig:
        return sig, entry, sl, target, "PULLBACK"

    entry = row["Close"]

    if entry <= row["SUPPORT"]*1.002:
        sl = row["SUPPORT"]*0.995
        return "BUY", entry, sl, entry + (entry - sl)*2, "SUPPORT"

    if entry >= row["RESISTANCE"]*0.998:
        sl = row["RESISTANCE"]*1.002
        return "SELL", entry, sl, entry - (sl - entry)*2, "RESISTANCE"

    if prev["Close"] < prev["EMA20"] and entry > row["EMA20"]:
        sl = row["EMA20"]*0.995
        return "BUY", entry, sl, entry + (entry - sl)*2, "EMA"

    if prev["Close"] > prev["EMA20"] and entry < row["EMA20"]:
        sl = row["EMA20"]*1.005
        return "SELL", entry, sl, entry - (sl - entry)*2, "EMA"

    return None, None, None, None, None

def ai_score(row, prev):
    score = 0
    if row["Close"] > row["EMA20"]: score += 2
    if big_player(row): score += 2
    if abs(row["Close"]-row["SUPPORT"]) < row["Close"]*0.003: score += 2
    if pullback_signal(row, prev)[0]: score += 3
    return score

def session_check(ts):
    return time(9,15) <= ts.time() <= time(15,30)

# ==========================================
# UI
# ==========================================
tab1, tab2 = st.tabs(["🚀 LIVE SCAN", "📊 BACKTEST"])

# LIVE
with tab1:
    if st.button("RUN LIVE SCAN"):
        data = get_data()

        for s in nse_200:
            try:
                df = data[s + ".NS"].dropna()
                if len(df) < 30: continue

                df = indicators(df)
                row, prev = df.iloc[-1], df.iloc[-2]
                ts = df.index[-1].tz_convert(IST)

                if not session_check(ts): continue

                score = ai_score(row, prev)
                sig, entry, sl, target, typ = signal_engine(row, prev)

                if sig and score >= 7:
                    st.session_state.live_logs.append({
                        "TIME": ts.strftime("%H:%M"),
                        "STOCK": s,
                        "SIGNAL": sig,
                        "ENTRY": round(entry,2),
                        "SL": round(sl,2),
                        "TARGET": round(target,2),
                        "SCORE": score,
                        "BIG PLAYER": "YES" if big_player(row) else "NO",
                        "PULLBACK": "YES" if typ=="PULLBACK" else "NO",
                        "TYPE": typ
                    })
            except:
                continue

    df_live = pd.DataFrame(st.session_state.live_logs)
    if not df_live.empty:
        st.dataframe(df_live, use_container_width=True)

        # Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            df_live.to_excel(writer, index=False)
        buffer.seek(0)

        st.download_button("⬇️ Download Excel", buffer, "LIVE_SIGNALS.xlsx")

# BACKTEST
with tab2:
    test_date = st.date_input("Select Date", now.date()-timedelta(days=1))

    if st.button("RUN BACKTEST"):
        data = get_data()
        logs = []

        for s in nse_200:
            try:
                df = data[s + ".NS"].dropna()
                df.index = df.index.tz_convert(IST)
                df = df[df.index.date == test_date]

                df = indicators(df)

                for i in range(1, len(df)):
                    row, prev = df.iloc[i], df.iloc[i-1]
                    ts = df.index[i]

                    if not session_check(ts): continue

                    score = ai_score(row, prev)
                    sig, entry, sl, target, typ = signal_engine(row, prev)

                    if sig and score >= 7:
                        logs.append({
                            "TIME": ts.strftime("%H:%M"),
                            "STOCK": s,
                            "SIGNAL": sig,
                            "ENTRY": round(entry,2),
                            "SL": round(sl,2),
                            "TARGET": round(target,2),
                            "SCORE": score,
                            "BIG PLAYER": "YES" if big_player(row) else "NO",
                            "PULLBACK": "YES" if typ=="PULLBACK" else "NO",
                            "TYPE": typ
                        })
            except:
                continue

        df_bt = pd.DataFrame(logs)
        if not df_bt.empty:
            st.dataframe(df_bt, use_container_width=True)

            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                df_bt.to_excel(writer, index=False)
            buffer.seek(0)

            st.download_button("⬇️ Download Backtest Excel", buffer, "BACKTEST.xlsx")
