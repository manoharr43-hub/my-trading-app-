import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz, io

st.set_page_config(page_title="🚀 NSE AI PRO V52.1", layout="wide")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V52.1 - FIXED SIGNAL SYSTEM")

# ✅ FULL NSE200
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
# SIGNAL LOGIC (LOOSE)
# ==========================================
def get_signal(row, prev):
    dist = abs(row['Close'] - row['EMA20']) / row['EMA20']

    # Pullback
    if dist < 0.012 and row['Close'] > row['EMA20']:
        return "BUY"
    if dist < 0.012 and row['Close'] < row['EMA20']:
        return "SELL"

    # Breakout
    if prev['Close'] < row['EMA20'] and row['Close'] > row['EMA20']:
        return "BUY"
    if prev['Close'] > row['EMA20'] and row['Close'] < row['EMA20']:
        return "SELL"

    return None

# ==========================================
# DATA
# ==========================================
@st.cache_data(ttl=120)
def get_data():
    return yf.download([s+".NS" for s in stocks],
                       period="5d", interval="5m", group_by="ticker")

data = get_data()

# ==========================================
# LIVE
# ==========================================
if st.button("🚀 SCAN LIVE"):
    results = []

    for s in stocks:
        try:
            df = data[s+".NS"].dropna()
            df = add_indicators(df)

            if len(df) < 30:
                continue

            row = df.iloc[-1]
            prev = df.iloc[-2]

            signal = get_signal(row, prev)
            if not signal:
                continue

            entry = round(row['Close'], 2)

            results.append({
                "STOCK": s,
                "SIGNAL": signal,
                "ENTRY": entry
            })

        except:
            continue

    st.write(f"Signals Found: {len(results)}")
    st.dataframe(pd.DataFrame(results))

# ==========================================
# BACKTEST
# ==========================================
d = st.date_input("Backtest Date", now.date() - timedelta(days=1))

if st.button("RUN BACKTEST"):
    logs = []

    for s in stocks:
        try:
            df_all = data[s+".NS"].dropna()
            df_all.index = df_all.index.tz_convert(IST)

            df = add_indicators(df_all[df_all.index.date == d])

            for i in range(20, len(df)):
                row = df.iloc[i]
                prev = df.iloc[i-1]

                signal = get_signal(row, prev)
                if not signal:
                    continue

                logs.append({
                    "TIME": df.index[i].strftime('%H:%M'),
                    "STOCK": s,
                    "SIGNAL": signal
                })

        except:
            continue

    st.write(f"Backtest Signals: {len(logs)}")
    st.dataframe(pd.DataFrame(logs))
