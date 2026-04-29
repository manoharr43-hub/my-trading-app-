import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta, time
import pytz
import io
from streamlit_autorefresh import st_autorefresh

# ==========================================
# CONFIG & SETUP
# ==========================================
st.set_page_config(page_title="🚀 NSE AI PRO V68 ELITE PRO", layout="wide")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V68 ELITE PRO")
st.write(f"🕒 Current Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")

# ఆటోమేటిక్ రిఫ్రెష్ (ప్రతి 1 నిమిషానికి)
st_autorefresh(interval=60000, key="refresh")

# Session State initialization
if "live_logs" not in st.session_state:
    st.session_state.live_logs = []
if "cooldown" not in st.session_state:
    st.session_state.cooldown = {}

# ==========================================
# NSE 200 STOCKS LIST
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
# DATA FETCHING (OPTIMIZED)
# ==========================================
@st.cache_data(ttl=300)
def get_data():
    # 30 రోజుల డేటా 5 నిమిషాల క్యాండిల్స్ తో
    return yf.download(tickers, period="30d", interval="5m", group_by="ticker", threads=True)

# ==========================================
# INDICATORS
# ==========================================
def indicators(df):
    df = df.copy()
    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()
    df["VOLAVG"] = df["Volume"].rolling(20).mean()

    # RSI Calculation
    delta = df["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))
    return df

# ==========================================
# TRADING LOGIC & SIGNALS
# ==========================================
def signal_engine(row, prev):
    if pd.isna(row["EMA20"]) or pd.isna(row["RSI"]): 
        return None, None, None, None, None

    sig, entry, sl, target = None, None, None, None
    
    # 1. PULLBACK BUY LOGIC
    if row["Close"] > row["EMA20"] and row["Low"] <= row["EMA20"] * 1.002:
        if row["EMA20"] > row["EMA50"] and row["RSI"] < 65:
            sig = "BUY"
            entry = row["Close"]
            sl = row["EMA20"] * 0.995
            target = entry + (entry - sl) * 2.5

    # 2. PULLBACK SELL LOGIC
    elif row["Close"] < row["EMA20"] and row["High"] >= row["EMA20"] * 0.998:
        if row["EMA20"] < row["EMA50"] and row["RSI"] > 35:
            sig = "SELL"
            entry = row["Close"]
            sl = row["EMA20"] * 1.005
            target = entry - (sl - entry) * 2.5

    return sig, entry, sl, target, "PULLBACK"

def ai_score(row):
    score = 0
    if row["Close"] > row["EMA20"]: score += 2
    if row["Volume"] > row["VOLAVG"] * 1.5: score += 2
    if 40 < row["RSI"] < 60: score += 2  # Mean reversion potential
    return score

def is_market_open(ts):
    return time(9, 15) <= ts.time() <= time(15, 30)

# ==========================================
# UI INTERFACE
# ==========================================
tab1, tab2 = st.tabs(["🚀 LIVE SCANNER", "📊 ACCURATE BACKTEST"])

# --- LIVE SCANNER ---
with tab1:
    if st.button("RUN LIVE SCAN"):
        with st.spinner("Fetching NSE Data..."):
            data = get_data()
            
        new_signals = []
        for s in nse_200:
            t_symbol = s + ".NS"
            if t_symbol not in data.columns.levels[0]: continue

            df = data[t_symbol].dropna()
            if len(df) < 50: continue

            df = indicators(df)
            row, prev = df.iloc[-1], df.iloc[-2]
            ts = df.index[-1].astimezone(IST)

            if not is_market_open(ts): continue

            # Cooldown check (30 mins)
            if s in st.session_state.cooldown:
                if (ts - st.session_state.cooldown[s]).total_seconds() < 1800:
                    continue

            sig, entry, sl, target, typ = signal_engine(row, prev)
            score = ai_score(row)

            if sig and score >= 4:
                st.session_state.cooldown[s] = ts
                st.session_state.live_logs.append({
                    "TIME": ts.strftime("%H:%M"),
                    "STOCK": s,
                    "SIGNAL": sig,
                    "ENTRY": round(entry, 2),
                    "SL": round(sl, 2),
                    "TARGET": round(target, 2),
                    "SCORE": score
                })

    if st.session_state.live_logs:
        df_live = pd.DataFrame(st.session_state.live_logs).drop_duplicates(subset=['STOCK', 'TIME'], keep='last')
        st.dataframe(df_live.sort_index(ascending=False), use_container_width=True)
        
        # Download
        csv = df_live.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Live Report", csv, "Live_Signals.csv", "text/csv")

# --- BACKTESTER (FIXED) ---
with tab2:
    col1, col2 = st.columns(2)
    test_date = col1.date_input("Backtest Date", now.date() - timedelta(days=1))
    
    if st.button("START BACKTEST"):
        with st.spinner(f"Backtesting for {test_date}..."):
            all_data = get_data()
            bt_logs = []
            target_dt_str = test_date.strftime('%Y-%m-%d')

            for s in nse_200:
                t_symbol = s + ".NS"
                if t_symbol not in all_data.columns.levels[0]: continue

                # Get data and filter for specific date
                df_full = all_data[t_symbol].dropna()
                df_full.index = df_full.index.tz_convert(IST)
                
                # Filter rows belonging to the test date
                df = df_full[df_full.index.strftime('%Y-%m-%d') == target_dt_str].copy()
                
                if len(df) < 20: continue
                
                df = indicators(df)
                
                for i in range(1, len(df)):
                    row, prev = df.iloc[i], df.iloc[i-1]
                    ts = df.index[i]
                    
                    sig, entry, sl, target, typ = signal_engine(row, prev)
                    
                    if sig:
                        result = "OPEN"
                        # Look ahead for result
                        for j in range(i+1, len(df)):
                            future = df.iloc[j]
                            if sig == "BUY":
                                if future["Low"] <= sl: result = "LOSS"; break
                                if future["High"] >= target: result = "WIN"; break
                            else:
                                if future["High"] >= sl: result = "LOSS"; break
                                if future["Low"] <= target: result = "WIN"; break
                        
                        bt_logs.append({
                            "TIME": ts.strftime("%H:%M"),
                            "STOCK": s,
                            "SIGNAL": sig,
                            "ENTRY": round(entry, 2),
                            "RESULT": result
                        })

            if bt_logs:
                df_bt = pd.DataFrame(bt_logs)
                st.dataframe(df_bt, use_container_width=True)
                
                # Stats
                wins = len(df_bt[df_bt["RESULT"] == "WIN"])
                losses = len(df_bt[df_bt["RESULT"] == "LOSS"])
                accuracy = (wins / (wins + losses)) * 100 if (wins + losses) > 0 else 0
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Total Trades", len(df_bt))
                c2.metric("Wins ✅", wins)
                c3.metric("Accuracy 🎯", f"{round(accuracy, 2)}%")
            else:
                st.warning("No signals found for the selected date. Try a different trading day.")
