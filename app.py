import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz, io
from streamlit_autorefresh import st_autorefresh

# ==========================================
# 1. CONFIGURATION (సెటప్)
# ==========================================
st.set_page_config(page_title="🚀 NSE AI PRO V48", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V48 - ADVANCED PULLBACK SYSTEM")
st.markdown(f"**🕒 Current Market Time (IST):** `{now.strftime('%Y-%m-%d %H:%M:%S')}`")

# ==========================================
# 2. NSE 200 STOCKS LIST
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
# 3. INDICATORS
# ==========================================
def add_indicators(df):
    if df.empty: return df
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

# ==========================================
# 4. LOGIC
# ==========================================
def get_pullback(close, ema20, vwap, prev_close):
    dist = abs(close - ema20) / ema20
    if dist < 0.004:
        if close > ema20 and close > vwap:
            return "SUPPORT BUY 🟢"
        elif close < ema20 and close < vwap:
            return "RESIST SELL 🔴"
    if prev_close < ema20 and close > ema20:
        return "RECENT BUY 🔼"
    elif prev_close > ema20 and close < ema20:
        return "RECENT SELL 🔽"
    return None

def best_trade(row):
    body = abs(row['Close'] - row['Open'])
    rng = row['High'] - row['Low']
    return body > rng * 0.5 and row['Volume'] > row['VolAvg'] * 2 and row['ATR'] > row['Close'] * 0.002

# ==========================================
# 5. FETCH DATA (FIXED FOR RUNTIME ERROR)
# ==========================================
@st.cache_data(ttl=60)
def get_data():
    # threads=False added to prevent threading errors in Streamlit Cloud
    return yf.download(
        [s+".NS" for s in stocks], 
        period="5d", 
        interval="5m", 
        group_by="ticker", 
        threads=False,
        progress=False
    )

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

# ==========================================
# 6. UI & TABS
# ==========================================
tab1, tab2 = st.tabs(["📊 LIVE TRADES", "🕒 HISTORICAL BACKTEST"])

try:
    data = get_data()
except Exception as e:
    st.error(f"Error fetching data: {e}")
    st.stop()

# --- LIVE TAB ---
with tab1:
    if st.button("🔍 SCAN LIVE NSE200"):
        out = []
        for s in stocks:
            try:
                ticker_df = data[s+".NS"].dropna()
                if len(ticker_df) < 20: continue
                
                df = add_indicators(ticker_df)
                l, prev = df.iloc[-1], df.iloc[-2]

                pull = get_pullback(l['Close'], l['EMA20'], l['VWAP'], prev['Close'])

                if pull and best_trade(l):
                    sig = "BUY" if "BUY" in pull else "SELL"
                    entry = round(l['Close'], 2)
                    out.append({
                        "TIME": df.index[-1].tz_convert(IST).strftime('%H:%M'),
                        "STOCK": s,
                        "SIGNAL": sig,
                        "TYPE": pull,
                        "ENTRY": entry,
                        "SL": round(entry - l['ATR']*1.5 if sig=="BUY" else entry + l['ATR']*1.5, 2),
                        "TGT": round(entry + l['ATR']*3 if sig=="BUY" else entry - l['ATR']*3, 2),
                        "BIG MOVE": "🔥" if l['Volume'] > l['VolAvg']*2.5 else "NO"
                    })
            except: continue

        if out:
            df_out = pd.DataFrame(out)
            st.success(f"Found {len(df_out)} Signals")
            st.dataframe(df_out, use_container_width=True)
            st.download_button("📥 Download Excel", to_excel(df_out), "NSE200_LIVE.xlsx")
        else:
            st.warning("No Pullback Trades Found.")

# --- BACKTEST TAB ---
with tab2:
    date_pick = st.date_input("Select Date", now.date() - timedelta(days=1))
    if st.button("🔄 RUN BACKTEST"):
        logs = []
        for s in stocks:
            try:
                df_all = data[s+".NS"].dropna()
                df_all.index = df_all.index.tz_convert(IST)
                day_df = df_all[df_all.index.date == date_pick]
                if len(day_df) < 20: continue
                
                df = add_indicators(day_df)

                for i in range(20, len(df)):
                    row, prev = df.iloc[i], df.iloc[i-1]
                    pull = get_pullback(row['Close'], row['EMA20'], row['VWAP'], prev['Close'])

                    if pull and best_trade(row):
                        sig = "BUY" if "BUY" in pull else "SELL"
                        entry = round(row['Close'], 2)
                        logs.append({
                            "TIME": df.index[i].strftime('%H:%M'),
                            "STOCK": s,
                            "SIGNAL": sig,
                            "TYPE": pull,
                            "ENTRY": entry,
                            "SL": round(entry - row['ATR']*1.5 if sig=="BUY" else entry + row['ATR']*1.5, 2),
                            "TGT": round(entry + row['ATR']*3 if sig=="BUY" else entry - row['ATR']*3, 2),
                            "BIG MOVE": "🔥" if row['Volume'] > row['VolAvg']*2.5 else "NO"
                        })
            except: continue

        if logs:
            df_log = pd.DataFrame(logs)
            st.dataframe(df_log, use_container_width=True)
            st.download_button("📥 Download Report", to_excel(df_log), f"Backtest_{date_pick}.xlsx")
        else:
            st.info("No Historical Signals found.")
