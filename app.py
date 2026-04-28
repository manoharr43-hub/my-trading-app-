import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz, io
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🚀 NSE AI PRO V47", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V47 - NSE200 PRO SYSTEM")
st.write(f"🕒 Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")

# =============================
# NSE 200 STOCKS
# =============================
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

# =============================
# INDICATORS
# =============================
def add_indicators(df):
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()

    tr = pd.concat([
        df['High'] - df['Low'],
        abs(df['High'] - df['Close'].shift()),
        abs(df['Low'] - df['Close'].shift())
    ], axis=1).max(axis=1)

    df['ATR'] = tr.rolling(14).mean()
    df['VolAvg'] = df['Volume'].rolling(20).mean()
    return df

# =============================
# PULLBACK LOGIC
# =============================
def get_pullback(close, ema20, vwap, prev_close):
    dist = abs(close - ema20) / ema20

    if dist < 0.004:
        if close > ema20 and close > vwap:
            return "SUPPORT BUY 🟢"
        elif close < ema20 and close < vwap:
            return "RESIST SELL 🔴"
    elif prev_close < ema20 and close > ema20:
        return "RECENT BUY 🔼"
    elif prev_close > ema20 and close < ema20:
        return "RECENT SELL 🔽"
    return None

# =============================
# FILTER
# =============================
def best_trade(row):
    body = abs(row['Close'] - row['Open'])
    rng = row['High'] - row['Low']
    return body > rng*0.5 and row['Volume'] > row['VolAvg']*2 and row['ATR'] > row['Close']*0.002

# =============================
# FETCH
# =============================
@st.cache_data(ttl=60)
def get_data():
    return yf.download([s+".NS" for s in stocks], period="5d", interval="5m", group_by="ticker")

data = get_data()

# =============================
# EXCEL
# =============================
def to_excel(df):
    output = io.BytesIO()
    df.to_excel(output, index=False)
    return output.getvalue()

# =============================
# TABS
# =============================
tab1, tab2 = st.tabs(["🔴 LIVE", "📊 BACKTEST"])

# =============================
# LIVE
# =============================
with tab1:
    if st.button("RUN LIVE NSE200"):
        out = []

        for s in stocks:
            try:
                df = add_indicators(data[s+".NS"].dropna())
                l, prev = df.iloc[-1], df.iloc[-2]

                pull = get_pullback(l['Close'], l['EMA20'], l['VWAP'], prev['Close'])

                if pull:
                    sig = "BUY" if "BUY" in pull else "SELL"

                    if best_trade(l):
                        entry = round(l['Close'],2)

                        out.append({
                            "TIME": df.index[-1].tz_convert(IST).strftime('%H:%M'),
                            "STOCK": s,
                            "SIGNAL": sig,
                            "PULLBACK": pull,
                            "ENTRY": entry,
                            "SL": round(entry - l['ATR']*1.5 if sig=="BUY" else entry + l['ATR']*1.5,2),
                            "TGT": round(entry + l['ATR']*3 if sig=="BUY" else entry - l['ATR']*3,2),
                            "BIG MOVE": "🔥" if l['Volume'] > l['VolAvg']*2.5 else "NO"
                        })
            except:
                continue

        if out:
            df_out = pd.DataFrame(out)
            st.dataframe(df_out, use_container_width=True)
            st.download_button("📥 Download", to_excel(df_out), "NSE200_LIVE.xlsx")
        else:
            st.warning("No Trades Found")

# =============================
# BACKTEST
# =============================
with tab2:
    date = st.date_input("Select Date", now.date()-timedelta(days=1))

    if st.button("RUN BACKTEST NSE200"):
        logs = []

        for s in stocks:
            try:
                df = data[s+".NS"].dropna()
                df.index = df.index.tz_convert(IST)
                df = add_indicators(df[df.index.date == date])

                for i in range(20, len(df)):
                    row, prev = df.iloc[i], df.iloc[i-1]

                    pull = get_pullback(row['Close'], row['EMA20'], row['VWAP'], prev['Close'])

                    if pull:
                        sig = "BUY" if "BUY" in pull else "SELL"

                        if best_trade(row):
                            entry = round(row['Close'],2)

                            logs.append({
                                "TIME": df.index[i].strftime('%H:%M'),
                                "STOCK": s,
                                "SIGNAL": sig,
                                "PULLBACK": pull,
                                "ENTRY": entry,
                                "SL": round(entry - row['ATR']*1.5 if sig=="BUY" else entry + row['ATR']*1.5,2),
                                "TGT": round(entry + row['ATR']*3 if sig=="BUY" else entry - row['ATR']*3,2),
                                "BIG MOVE": "🔥" if row['Volume'] > row['VolAvg']*2.5 else "NO"
                            })
            except:
                continue

        if logs:
            df_log = pd.DataFrame(logs)
            st.dataframe(df_log, use_container_width=True)
            st.download_button("📥 Download", to_excel(df_log), "NSE200_BACKTEST.xlsx")
        else:
            st.warning("No Trades Found")
