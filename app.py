import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz, io

# ==========================================
# 1. CONFIGURATION
# ==========================================
st.set_page_config(page_title="🚀 NSE AI PRO V48 - STABLE", layout="wide")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V48 - ULTIMATE STABLE")
st.markdown(f"**🕒 IST Time:** `{now.strftime('%Y-%m-%d %H:%M:%S')}`")

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
# 3. INDICATORS LOGIC
# ==========================================
def add_indicators(df):
    if df is None or df.empty: return None
    df = df.copy()
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

def get_pullback(close, ema20, vwap, prev_close):
    dist = abs(close - ema20) / ema20
    if dist < 0.004:
        if close > ema20 and close > vwap: return "SUPPORT BUY 🟢"
        elif close < ema20 and close < vwap: return "RESIST SELL 🔴"
    if prev_close < ema20 and close > ema20: return "RECENT BUY 🔼"
    elif prev_close > ema20 and close < ema20: return "RECENT SELL 🔽"
    return None

def best_trade(row):
    body = abs(row['Close'] - row['Open'])
    rng = row['High'] - row['Low']
    return body > rng * 0.5 and row['Volume'] > row['VolAvg'] * 2 and row['ATR'] > row['Close'] * 0.002

# ==========================================
# 4. SAFE FETCH (DITCHING MULTI-THREADING)
# ==========================================
@st.cache_data(ttl=300) # 5 mins cache
def get_safe_data():
    all_data = {}
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, s in enumerate(stocks):
        symbol = s + ".NS"
        status_text.text(f"Fetching {symbol}...")
        try:
            # Single ticker download is 100% safe from threading errors
            d = yf.download(symbol, period="5d", interval="5m", progress=False, threads=False)
            if not d.empty:
                all_data[symbol] = d
        except:
            continue
        progress_bar.progress((i + 1) / len(stocks))
    
    status_text.empty()
    progress_bar.empty()
    return all_data

def to_csv(df):
    return df.to_csv(index=False).encode('utf-8')

# ==========================================
# 5. UI TABS
# ==========================================
tab1, tab2 = st.tabs(["📊 LIVE SIGNALS", "🕒 BACKTEST"])

# --- LIVE ---
with tab1:
    if st.button("🚀 START REAL-TIME SCAN"):
        data_dict = get_safe_data()
        out = []
        
        for s in stocks:
            symbol = s + ".NS"
            if symbol in data_dict:
                df = add_indicators(data_dict[symbol])
                if df is None or len(df) < 20: continue
                
                l, prev = df.iloc[-1], df.iloc[-2]
                pull = get_pullback(l['Close'], l['EMA20'], l['VWAP'], prev['Close'])

                if pull and best_trade(l):
                    sig = "BUY" if "BUY" in pull else "SELL"
                    entry = round(float(l['Close']), 2)
                    out.append({
                        "TIME": df.index[-1].astimezone(IST).strftime('%H:%M'),
                        "STOCK": s,
                        "SIGNAL": sig,
                        "TYPE": pull,
                        "ENTRY": entry,
                        "SL": round(entry - l['ATR']*1.5 if sig=="BUY" else entry + l['ATR']*1.5, 2),
                        "TGT": round(entry + l['ATR']*3 if sig=="BUY" else entry - l['ATR']*3, 2),
                        "BIG MOVE": "🔥" if l['Volume'] > l['VolAvg']*2.5 else "NO"
                    })

        if out:
            res_df = pd.DataFrame(out)
            st.success(f"Scanned {len(stocks)} stocks. Found {len(res_df)} trades.")
            st.dataframe(res_df, use_container_width=True)
            st.download_button("📥 Download Results", to_csv(res_df), "NSE_LIVE.csv", "text/csv")
        else:
            st.warning("No signals found right now.")

# --- BACKTEST ---
with tab2:
    date_pick = st.date_input("Backtest Date", now.date() - timedelta(days=1))
    if st.button("🔄 RUN BACKTEST"):
        data_dict = get_safe_data()
        logs = []
        
        for s in stocks:
            symbol = s + ".NS"
            if symbol in data_dict:
                df_all = data_dict[symbol]
                df_all.index = df_all.index.tz_convert(IST)
                day_df = df_all[df_all.index.date == date_pick]
                
                if len(day_df) < 20: continue
                df = add_indicators(day_df)
                if df is None: continue

                for i in range(20, len(df)):
                    row, prev = df.iloc[i], df.iloc[i-1]
                    pull = get_pullback(row['Close'], row['EMA20'], row['VWAP'], prev['Close'])

                    if pull and best_trade(row):
                        sig = "BUY" if "BUY" in pull else "SELL"
                        entry = round(float(row['Close']), 2)
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

        if logs:
            back_df = pd.DataFrame(logs)
            st.dataframe(back_df, use_container_width=True)
            st.download_button("📥 Download Report", to_csv(back_df), f"Backtest_{date_pick}.csv", "text/csv")
        else:
            st.info("No signals for this date.")
