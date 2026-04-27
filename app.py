import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from streamlit_autorefresh import st_autorefresh
import io

# =============================
# CONFIG & UI SETUP
# =============================
st.set_page_config(page_title="🚀 NSE AI PRO V40 (NSE 200)", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V40 - NSE 200 MASTER SCANNER")
st.write(f"🕒 **Market Time:** {now.strftime('%Y-%m-%d %H:%M:%S')}")

# =============================
# NSE 200 STOCK LIST (TOP 200)
# =============================
stocks = [
    "ABB","ACC","ADANIENT","ADANIPORTS","ADANIPOWER","ATGL","AWL","ABCAPITAL","ABFRL",
    "ALKEM","AMBUJACEM","APOLLOHOSP","APOLLOTYRE","ASHOKLEY","ASIANPAINT","ASTRAL","AUBANK",
    "AUROPHARMA","AXISBANK","BAJAJ-AUTO","BAJFINANCE","BAJAJFINSV","BAJAJHLDNG","BALKRISIND",
    "BANDHANBNK","BANKBARODA","BANKINDIA","BEL","BERGEPAINT","BHARATFORG","BHARTIARTL","BIOCON",
    "BOSCHLTD","BPCL","BRITANNIA","BSOFT","CANBK","CGPOWER","CHOLAFIN","CIPLA","COALINDIA",
    "COFORGE","COLPAL","CONCOR","CUMMINSIND","DLF","DABUR","DALBHARAT","DEEPAKNTR","DIVISLAB",
    "DIXON","DRREDDY","EICHERMOT","ESCORTS","EXIDEIND","FEDERALBNK","FORTIS","GAIL","GLENMARK",
    "GMRINFRA","GODREJCP","GODREJPROP","GRASIM","GUJGASLTD","HAL","HAVELLS","HCLTECH","HDFCBANK",
    "HDFCLIFE","HEROMOTOCO","HINDALCO","HINDCOPPER","HINDPETRO","HINDUNILVR","ICICIBANK",
    "ICICIGI","ICICIPRULI","IDFCFIRSTB","IEX","IGL","INDHOTEL","INDIACEM","INDIAMART",
    "INDIGO","INDUSINDBK","INDUSTOWER","INFY","IOC","IRCTC","IRFC","ITC","JINDALSTEL",
    "JSWENERGY","JSWSTEEL","JUBLFOOD","KOTAKBANK","L&TFH","LT","LTIM","LTTS","LICHSGFIN",
    "LUPIN","M&M","M&MFIN","MANAPPURAM","MARICO","MARUTI","MCDOWELL-N","MCX","METROPOLIS",
    "MFSL","MGL","MOTHERSON","MPHASIS","MRF","MUTHOOTFIN","NATIONALUM","NAVINFLUOR","NESTLEIND",
    "NMDC","NTPC","OBEROIRLTY","ONGC","PAGEIND","PEL","PERSISTENT","PETRONET","PFC","PIDILITIND",
    "PIIND","PNB","POLYCAB","POWERCGRID","PRESTIGE","RELIANCE","SAIL","SBICARD","SBILIFE","SBIN",
    "SHREECEM","SHRIRAMFIN","SIEMENS","SRF","SUNPHARMA","SUNTV","SYNGENE","TATACOMM","TATACONSUM",
    "TATAELXSI","TATAMOTORS","TATAPOWER","TATASTEEL","TCS","TECHM","TITAN","TORNTPHARM","TRENT",
    "TVSMOTOR","UBL","ULTRACEMCO","UPL","VBL","VEDL","VOLTAS","WIPRO","YESBANK","ZEEL","ZOMATO"
    # గమనిక: ఇక్కడ కొన్ని ముఖ్యమైన స్టాక్స్ ఇచ్చాను, మీరు అవసరమైతే మరిన్ని జోడించవచ్చు.
]

# =============================
# INDICATORS (V40)
# =============================
def add_indicators(df):
    df = df.copy()
    if len(df) < 20: return df
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-9)
    high_low = df['High'] - df['Low']
    tr = pd.concat([high_low, abs(df['High'] - df['Close'].shift()), abs(df['Low'] - df['Close'].shift())], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()
    df['VolAvg'] = df['Volume'].rolling(20).mean()
    return df

@st.cache_data(ttl=60)
def fetch_data(symbols, interval, period):
    tickers = [s + ".NS" for s in symbols]
    return yf.download(tickers, period=period, interval=interval, group_by='ticker', progress=False)

# డేటా లోడింగ్ - NSE 200 కాబట్టి కొంచెం టైమ్ తీసుకుంటుంది
with st.spinner("Fetching NSE 200 Data... Please wait"):
    data_5m = fetch_data(stocks, "5m", "5d")

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='NSE_200_Report')
    return output.getvalue()

# =============================
# TABS
# =============================
tab1, tab2 = st.tabs(["🔍 NSE 200 LIVE SCANNER", "📊 NSE 200 BACKTEST"])

# -----------------------------
# TAB 1: LIVE SCANNER
# -----------------------------
with tab1:
    if st.button("EXECUTE 200 STOCK SCAN"):
        live_res = []
        for s in stocks:
            try:
                stock_data = data_5m.get(s + ".NS")
                if stock_data is None or stock_data.empty: continue
                
                df = add_indicators(stock_data.dropna())
                l = df.iloc[-1]
                dist = abs(l['Close'] - l['EMA20']) / l['EMA20']
                
                if dist < 0.004:
                    signal = "None"
                    if l['Close'] > l['VWAP'] and l['Close'] > l['Open']: signal = "BUY 🟢"
                    elif l['Close'] < l['VWAP'] and l['Close'] < l['Open']: signal = "SELL 🔴"
                    
                    if signal != "None":
                        atr = l['ATR']
                        entry = round(l['Close'], 2)
                        live_res.append({
                            "TIME": df.index[-1].astimezone(IST).strftime('%H:%M'),
                            "STOCK": s, "SIGNAL": signal,
                            "BIG PLAYER": "🔥 YES" if l['Volume'] > (l['VolAvg'] * 2.5) else "-",
                            "ENTRY": entry,
                            "STOP LOSS": round(entry - (atr*1.5) if "BUY" in signal else entry + (atr*1.5), 2),
                            "TARGET": round(entry + (atr*3) if "BUY" in signal else entry - (atr*3), 2)
                        })
            except: continue
        if live_res:
            res_df = pd.DataFrame(live_res)
            st.dataframe(res_df, use_container_width=True)
            st.download_button("📥 Excel Export", data=to_excel(res_df), file_name="NSE200_Live_Scan.xlsx")
        else: st.info("No active signals in NSE 200 stocks.")

# -----------------------------
# TAB 2: BACKTEST (NSE 200)
# -----------------------------
with tab2:
    bt_date = st.date_input("Select Date", value=now.date() - timedelta(days=1))
    if st.button("RUN NSE 200 BACKTEST"):
        bt_results = []
        for s in stocks:
            try:
                df_raw = data_5m.get(s + ".NS")
                if df_raw is None: continue
                
                df = df_raw.dropna().copy()
                df.index = df.index.tz_convert(IST)
                df_day = add_indicators(df[df.index.date == bt_date])
                if df_day is None or df_day.empty: continue

                last_action, last_time = None, None

                for i in range(15, len(df_day)):
                    row = df_day.iloc[i]
                    curr_time = df_day.index[i]
                    dist = abs(row['Close'] - row['EMA20']) / row['EMA20']
                    
                    if dist < 0.004:
                        curr_sig = "None"
                        if row['Close'] > row['VWAP'] and row['Close'] > row['Open']: curr_sig = "BUY 🟢"
                        elif row['Close'] < row['VWAP'] and row['Close'] < row['Open']: curr_sig = "SELL 🔴"
                        
                        if curr_sig != "None":
                            # Trend Reversal & Cooldown
                            if curr_sig != last_action or (last_time and (curr_time - last_time) > timedelta(minutes=60)):
                                entry = round(row['Close'], 2)
                                bt_results.append({
                                    "TIME": curr_time.strftime('%H:%M'),
                                    "STOCK": s, "ACTION": curr_sig,
                                    "BIG PLAYER": "🔥" if row['Volume'] > row['VolAvg']*2.5 else "-",
                                    "ENTRY": entry,
                                    "SL": round(entry - (row['ATR']*1.5) if "BUY" in curr_sig else entry + (row['ATR']*1.5), 2),
                                    "TGT": round(entry + (row['ATR']*3) if "BUY" in curr_sig else entry - (row['ATR']*3), 2)
                                })
                                last_action, last_time = curr_sig, curr_time
            except: continue
            
        if bt_results:
            bt_df = pd.DataFrame(bt_results)
            st.dataframe(bt_df, use_container_width=True)
        else: st.warning("No trend reversal signals found.")
