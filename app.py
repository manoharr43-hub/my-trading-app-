import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz, io
from streamlit_autorefresh import st_autorefresh

# ==========================================
# CONFIG
# ==========================================
st.set_page_config(page_title="🚀 NSE AI PRO V50.1", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V50.1 - NSE200 ADAPTIVE SCANNER")
st.write(f"🕒 {now.strftime('%Y-%m-%d %H:%M:%S')}")

# ==========================================
# NSE 200 STOCK LIST
# ==========================================
stocks = [
"RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","BHARTIARTL","ITC","KOTAKBANK","LT",
"HINDUNILVR","ASIANPAINT","AXISBANK","MARUTI","SUNPHARMA","TITAN","ULTRACEMCO","WIPRO","NESTLEIND",
"POWERGRID","NTPC","BAJFINANCE","BAJAJFINSV","ONGC","ADANIENT","ADANIPORTS","JSWSTEEL","TATASTEEL",
"HCLTECH","TECHM","GRASIM","DIVISLAB","DRREDDY","CIPLA","BRITANNIA","EICHERMOT","HEROMOTOCO",
"TATAMOTORS","M&M","COALINDIA","BPCL","IOC","SHREECEM","HAVELLS","SIEMENS","DLF","PIDILITIND",
"INDUSINDBK","BANKBARODA","PNB","CANBK","FEDERALBNK","IDFCFIRSTB","YESBANK","ZEEL","ZOMATO",
"BEL","LTIM","ABB","ABCAPITAL","ABFRL","ACC","ADANIGREEN","ADANITRANS","ALKEM","AMBUJACEM",
"APOLLOHOSP","APOLLOTYRE","ASHOKLEY","ASTRAL","ATUL","AUROPHARMA","BAJAJHLDNG","BALKRISIND",
"BANDHANBNK","BERGEPAINT","BIOCON","BOSCHLTD","CHOLAFIN","COLPAL","CONCOR","CROMPTON","DABUR",
"DALBHARAT","DEEPAKNTR","DELHIVERY","ESCORTS","EXIDEIND","GAIL","GLENMARK","GMRINFRA",
"GNFC","GODREJCP","GODREJPROP","HAL","HINDALCO","HINDCOPPER","ICICIGI","ICICIPRULI",
"IGL","INDIGO","INDUSTOWER","IRCTC","JINDALSTEL","JSWENERGY","JUBLFOOD","LALPATHLAB",
"LICHSGFIN","LUPIN","MARICO","MFSL","MGL","MPHASIS","MUTHOOTFIN","NAM-INDIA",
"NAUKRI","NMDC","OBEROIRLTY","OFSS","PAGEIND","PEL","PETRONET","PIIND",
"POLYCAB","PVRINOX","RAMCOCEM","RECLTD","SAIL","SBICARD","SBILIFE","SRF",
"SUNTV","SYNGENE","TATACHEM","TATACOMM","TATAELXSI","TORNTPHARM","TORNTPOWER",
"TRENT","TVSMOTOR","UBL","UNIONBANK","UPL","VEDL","VOLTAS","WHIRLPOOL","ZYDUSLIFE"
]

# ==========================================
# INDICATORS
# ==========================================
def add_indicators(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    df['Date'] = df.index.date
    df['VWAP'] = df.groupby('Date').apply(
        lambda x: (x['Close']*x['Volume']).cumsum() / x['Volume'].cumsum()
    ).reset_index(level=0, drop=True)

    tr = pd.concat([
        df['High'] - df['Low'],
        abs(df['High'] - df['Close'].shift()),
        abs(df['Low'] - df['Close'].shift())
    ], axis=1).max(axis=1)

    df['ATR'] = tr.rolling(14).mean()
    df['VolAvg'] = df['Volume'].rolling(20).mean()

    return df

# ==========================================
# MARKET MODE
# ==========================================
@st.cache_data(ttl=60)
def get_market_mode():
    try:
        nifty = yf.download("^NSEI", period="1d", interval="5m")

        if isinstance(nifty.columns, pd.MultiIndex):
            nifty.columns = nifty.columns.get_level_values(0)

        if len(nifty) < 20:
            return "SLOW"

        move = abs(nifty['Close'].iloc[-1] - nifty['Close'].iloc[-5])

        if move > nifty['Close'].iloc[-1] * 0.005:
            return "TRENDING"
        else:
            return "SLOW"
    except:
        return "SLOW"

# ==========================================
# SIGNAL LOGIC
# ==========================================
def get_signal(row, mode):
    dist = abs(row['Close'] - row['EMA20']) / row['EMA20']
    limit = 0.004 if mode == "TRENDING" else 0.01

    if dist < limit and row['Close'] > row['EMA20'] and row['Close'] > row['VWAP']:
        return "BUY"

    if dist < limit and row['Close'] < row['EMA20'] and row['Close'] < row['VWAP']:
        return "SELL"

    return None

# ==========================================
# SCORE
# ==========================================
def valid_trade(row, mode):
    score = 0
    if row['Volume'] > row['VolAvg'] * 2:
        score += 1
    if row['ATR'] > row['Close'] * 0.002:
        score += 1

    return score >= (2 if mode=="TRENDING" else 1)

# ==========================================
# DATA FETCH (OPTIMIZED)
# ==========================================
@st.cache_data(ttl=120)
def get_data():
    try:
        return yf.download([s+".NS" for s in stocks],
                           period="5d", interval="5m", group_by="ticker", threads=True)
    except:
        return {}

def to_excel(df):
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    return buf.getvalue()

# ==========================================
# UI
# ==========================================
mode = get_market_mode()
st.write(f"📊 Market Mode: {mode}")

data = get_data()

if st.button("🚀 SCAN NSE200"):
    results = []

    for s in stocks:
        try:
            df = data.get(s+".NS")
            if df is None or df.empty:
                continue

            df = add_indicators(df.dropna())
            if len(df) < 30:
                continue

            row = df.iloc[-1]
            signal = get_signal(row, mode)

            if not signal:
                continue

            if not valid_trade(row, mode):
                continue

            entry = round(row['Close'], 2)

            results.append({
                "TIME": df.index[-1].tz_convert(IST).strftime('%H:%M'),
                "STOCK": s,
                "SIGNAL": signal,
                "ENTRY": entry,
                "SL": round(entry - row['ATR']*1.5 if signal=="BUY" else entry + row['ATR']*1.5, 2),
                "TGT": round(entry + row['ATR']*3 if signal=="BUY" else entry - row['ATR']*3, 2),
                "MODE": mode
            })

        except:
            continue

    if results:
        df_out = pd.DataFrame(results)
        st.success(f"Found {len(df_out)} signals")
        st.dataframe(df_out, use_container_width=True)
        st.download_button("📥 Download", to_excel(df_out), "NSE200_signals.xlsx")
    else:
        st.warning("No signals (market condition)")
