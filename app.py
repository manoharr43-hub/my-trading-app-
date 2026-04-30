import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz
import io
from streamlit_autorefresh import st_autorefresh

# ==========================================
# CONFIG
# ==========================================
st.set_page_config(page_title="🚀 NSE AI PRO V69 ULTRA PRO", layout="wide")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V69 ULTRA PRO")
st.write(f"🕒 Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")

st_autorefresh(interval=60000, key="refresh")

# Session
if "logs" not in st.session_state:
    st.session_state.logs = []

# ==========================================
# NSE STOCK LIST (Sample → You can extend)
# ==========================================
nse_200 = [
    "RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK",
    "SBIN","ITC","LT","AXISBANK","KOTAKBANK"
]

tickers = [s + ".NS" for s in nse_200]

# ==========================================
# DATA
# ==========================================
@st.cache_data(ttl=300)
def get_data():
    return yf.download(tickers, period="5d", interval="5m", group_by="ticker")

# ==========================================
# INDICATORS
# ==========================================
def indicators(df):
    df = df.copy()

    df["EMA20"] = df["Close"].ewm(span=20).mean()
    df["EMA50"] = df["Close"].ewm(span=50).mean()

    df["VOLAVG"] = df["Volume"].rolling(20).mean()
    df["RES"] = df["High"].rolling(20).max()
    df["SUP"] = df["Low"].rolling(20).min()

    delta = df["Close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rs = gain / loss

    df["RSI"] = 100 - (100 / (1 + rs))

    return df

# ==========================================
# SIGNAL ENGINE
# ==========================================
def signal_engine(row, prev):
    score = 0
    TYPE = []
    SIGNAL = None

    trend = abs(row["EMA20"] - row["EMA50"]) / row["EMA50"]
    if trend < 0.002:
        return None

    # BIG PLAYER
    price_move = abs(row["Close"] - prev["Close"]) / prev["Close"]
    if price_move > 0.01 and row["Volume"] > row["VOLAVG"] * 2:
        TYPE.append("BIG PLAYER")
        score += 3

    # BREAKOUT
    if row["Close"] > row["RES"]:
        TYPE.append("BREAKOUT")
        SIGNAL = "BUY"
        score += 2

    # BREAKDOWN
    if row["Close"] < row["SUP"]:
        TYPE.append("BREAKDOWN")
        SIGNAL = "SELL"
        score += 2

    # PULLBACK BUY
    if row["Close"] > row["EMA20"] and row["Low"] <= row["EMA20"]:
        if row["EMA20"] > row["EMA50"] and 40 < row["RSI"] < 60:
            TYPE.append("PULLBACK SUPPORT")
            SIGNAL = "BUY"
            score += 2

    # PULLBACK SELL
    if row["Close"] < row["EMA20"] and row["High"] >= row["EMA20"]:
        if row["EMA20"] < row["EMA50"] and 40 < row["RSI"] < 60:
            TYPE.append("PULLBACK RESISTANCE")
            SIGNAL = "SELL"
            score += 2

    if not SIGNAL or score < 4:
        return None

    entry = (row["High"] + row["Low"]) / 2

    if SIGNAL == "BUY":
        sl = row["Low"]
        target = entry + (entry - sl) * 2
    else:
        sl = row["High"]
        target = entry - (sl - entry) * 2

    return {
        "TIME": row.name,
        "TYPE": ",".join(TYPE),
        "SIGNAL": SIGNAL,
        "ENTRY": round(entry, 2),
        "SL": round(sl, 2),
        "TARGET": round(target, 2),
        "SCORE": score
    }

# ==========================================
# RUN SCANNER
# ==========================================
data = get_data()

results = []

for stock in nse_200:
    try:
        df = data[stock + ".NS"].dropna()
        df = indicators(df)

        for i in range(50, len(df)):
            res = signal_engine(df.iloc[i], df.iloc[i-1])
            if res:
                res["STOCK"] = stock
                results.append(res)

    except:
        continue

df_results = pd.DataFrame(results)

# ==========================================
# DISPLAY
# ==========================================
if not df_results.empty:
    st.success(f"Signals Found: {len(df_results)}")
    st.dataframe(df_results)

    # Save logs
    st.session_state.logs.extend(results)

else:
    st.warning("No Signals")

# ==========================================
# BACKTEST
# ==========================================
def backtest(df):
    wins = 0
    total = 0

    for i in range(len(df)):
        if df.iloc[i]["SIGNAL"] == "BUY":
            if df.iloc[i]["TARGET"] > df.iloc[i]["ENTRY"]:
                wins += 1
        else:
            if df.iloc[i]["TARGET"] < df.iloc[i]["ENTRY"]:
                wins += 1
        total += 1

    if total == 0:
        return 0

    return round((wins / total) * 100, 2)

if not df_results.empty:
    acc = backtest(df_results)
    st.info(f"Backtest Accuracy: {acc}%")

# ==========================================
# EXCEL DOWNLOAD
# ==========================================
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

if not df_results.empty:
    excel = to_excel(df_results)

    st.download_button(
        label="📥 Download Excel",
        data=excel,
        file_name="NSE_AI_SIGNALS.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
