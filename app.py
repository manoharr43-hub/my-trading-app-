import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta, time
import pytz
import io
from streamlit_autorefresh import st_autorefresh

# ==========================================
# CONFIG
# ==========================================
st.set_page_config(page_title="🚀 NSE AI PRO V68 ELITE PRO", layout="wide")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V68 ELITE PRO")
st.write(f"🕒 {now.strftime('%Y-%m-%d %H:%M:%S')}")

st_autorefresh(interval=60000, key="refresh")

# ==========================================
# SESSION
# ==========================================
if "live_logs" not in st.session_state:
    st.session_state.live_logs = []

if "cooldown" not in st.session_state:
    st.session_state.cooldown = {}

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
"CONCOR","MPHASIS","LTIM","PERSISTENT","COFORGE","RECLTD","PFC","IRFC",
"TATACHEM","CHOLAFIN","LICHSGFIN","MFSL","TORNTPHARM","GLENMARK","SUNTV","ZEEL",
"TV18BRDCST","BHEL","NHPC","SJVN","NLCINDIA","ATGL","IGL","MGL","PETRONET",
"JUBLFOOD","DEVYANI","TATAELXSI","KPITTECH","LTTS","HONAUT","3MINDIA","AARTIIND",
"DEEPAKNTR","LALPATHLAB","METROPOLIS","RAIN","TATAPOWER","TORNTPOWER","ADANIENSOL",
"ASTRAL","SUPREMEIND","FINCABLES","KEI","CROMPTON","VOLTAS","BLUESTARCO",
"UNITDSPR","UBL","RADICO","EMAMILTD","PATANJALI","FORTIS","MAXHEALTH",
"KIMS","MEDANTA","ROUTE","TANLA","AFFLE","INTELLECT","NEWGEN","CYIENT",
"ZENSARTECH","SONATSOFTW","RAMCOCEM","JKCEMENT","HEIDELBERG","DALBHARAT",
"OBEROIRLTY","PRESTIGE","BRIGADE","PHOENIXLTD","INDHOTEL","LEMONTREE",
"EDELWEISS","IIFL","360ONE","CUB","KARURVYSYA","SOUTHBANK","UJJIVANSFB",
"EQUITASBNK","CAMS","CDSL","MCX","BSE","ANGELONE","5PAISA",
"NYKAA","FSN","POLICYBZR","EASEMYTRIP","IRCON","RVNL","NBCC","HUDCO"
]

tickers = [s + ".NS" for s in nse_200]

# ==========================================
# DATA
# ==========================================
@st.cache_data(ttl=300)
def get_data():
    return yf.download(tickers, period="30d", interval="5m", group_by="ticker")

# ==========================================
# INDICATORS
# ==========================================
def indicators(df):
    df["EMA20"] = df["Close"].ewm(span=20).mean()
    df["EMA50"] = df["Close"].ewm(span=50).mean()
    df["SUPPORT"] = df["Low"].rolling(20).min()
    df["RESISTANCE"] = df["High"].rolling(20).max()
    df["VOLAVG"] = df["Volume"].rolling(20).mean()

    delta = df["Close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))

    return df

# ==========================================
# LOGIC
# ==========================================
def big_player(row):
    return row["Volume"] > row["VOLAVG"] * 1.5 if pd.notna(row["VOLAVG"]) else False

def signal_engine(row, prev):
    if pd.isna(row["EMA20"]): return None, None, None, None, None

    # Pullback
    if row["Close"] > row["EMA20"] and row["Low"] <= row["EMA20"]*1.002:
        sig = "BUY"
        entry = row["Close"]
        sl = row["EMA20"]*0.995
        target = entry + (entry - sl)*2.5
    elif row["Close"] < row["EMA20"] and row["High"] >= row["EMA20"]*0.998:
        sig = "SELL"
        entry = row["Close"]
        sl = row["EMA20"]*1.005
        target = entry - (sl - entry)*2.5
    else:
        return None, None, None, None, None

    # Filters
    if sig == "BUY" and row["RSI"] > 60: return None, None, None, None, None
    if sig == "SELL" and row["RSI"] < 40: return None, None, None, None, None

    if sig == "BUY" and row["EMA20"] < row["EMA50"]: return None, None, None, None, None
    if sig == "SELL" and row["EMA20"] > row["EMA50"]: return None, None, None, None, None

    return sig, entry, sl, target, "PULLBACK"

def ai_score(row):
    score = 0
    if row["Close"] > row["EMA20"]: score += 2
    if big_player(row): score += 2
    if row["RSI"] > 50: score += 2
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
                if (s + ".NS") not in data.columns.levels[0]:
                    continue

                df = data[s + ".NS"].dropna().copy()
                if len(df) < 50: continue

                df = indicators(df)
                row, prev = df.iloc[-1], df.iloc[-2]
                ts = df.index[-1].tz_convert(IST)

                if not session_check(ts): continue

                # Cooldown
                if s in st.session_state.cooldown:
                    if (ts - st.session_state.cooldown[s]).seconds < 1800:
                        continue

                sig, entry, sl, target, typ = signal_engine(row, prev)
                score = ai_score(row)

                if sig and score >= 5:
                    st.session_state.cooldown[s] = ts

                    st.session_state.live_logs.append({
                        "TIME": ts.strftime("%H:%M"),
                        "STOCK": s,
                        "SIGNAL": sig,
                        "ENTRY": round(entry,2),
                        "SL": round(sl,2),
                        "TARGET": round(target,2),
                        "SCORE": score,
                        "TYPE": typ
                    })
            except:
                continue

    df_live = pd.DataFrame(st.session_state.live_logs)

    if not df_live.empty:
        df_live = df_live.sort_values("SCORE", ascending=False)
        st.dataframe(df_live, use_container_width=True)

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
                if (s + ".NS") not in data.columns.levels[0]:
                    continue

                df = data[s + ".NS"].dropna().copy()
                df.index = df.index.tz_convert(IST)
                df = df[df.index.date == test_date]

                df = indicators(df)

                for i in range(1, len(df)):
                    row, prev = df.iloc[i], df.iloc[i-1]
                    ts = df.index[i]

                    if not session_check(ts): continue

                    sig, entry, sl, target, typ = signal_engine(row, prev)

                    if sig:
                        result = "OPEN"

                        for j in range(i+1, len(df)):
                            future = df.iloc[j]

                            if sig == "BUY":
                                if future["Low"] <= sl:
                                    result = "LOSS"
                                    break
                                if future["High"] >= target:
                                    result = "WIN"
                                    break

                            if sig == "SELL":
                                if future["High"] >= sl:
                                    result = "LOSS"
                                    break
                                if future["Low"] <= target:
                                    result = "WIN"
                                    break

                        logs.append({
                            "TIME": ts.strftime("%H:%M"),
                            "STOCK": s,
                            "SIGNAL": sig,
                            "ENTRY": round(entry,2),
                            "SL": round(sl,2),
                            "TARGET": round(target,2),
                            "RESULT": result,
                            "TYPE": typ
                        })
            except:
                continue

        df_bt = pd.DataFrame(logs)

        if not df_bt.empty:
            st.dataframe(df_bt, use_container_width=True)

            wins = df_bt[df_bt["RESULT"]=="WIN"].shape[0]
            total = len(df_bt)
            acc = (wins/total)*100 if total>0 else 0

            st.success(f"🎯 Accuracy: {round(acc,2)}%")

            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                df_bt.to_excel(writer, index=False)
            buffer.seek(0)

            st.download_button("⬇️ Download Backtest Excel", buffer, "BACKTEST.xlsx")
