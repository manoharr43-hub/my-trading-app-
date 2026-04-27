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
st.set_page_config(page_title="🚀 NSE AI PRO V41", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V41 - PULLBACK & REVERSAL MASTER")
st.write(f"🕒 **Market Time:** {now.strftime('%Y-%m-%d %H:%M:%S')}")

# =============================
# NSE 200 STOCK LIST
# =============================
stocks = [
    "ABB","ACC","ADANIENT","ADANIPORTS","ADANIPOWER","ATGL","AWL","ABCAPITAL","ABFRL",
    "ALKEM","AMBUJACEM","APOLLOHOSP","APOLLOHOSP","ASHOKLEY","ASIANPAINT","ASTRAL","AUBANK",
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
]

# =============================
# INDICATORS
# =============================
def add_indicators(df):
    df = df.copy()
    if len(df) < 20: return df
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-9)
    # ATR for dynamic SL/Tgt
    high_low = df['High'] - df['Low']
    tr = pd.concat([high_low, abs(df['High'] - df['Close'].shift()), abs(df['Low'] - df['Close'].shift())], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()
    # Volume Avg
    df['VolAvg'] = df['Volume'].rolling(20).mean()
    return df

@st.cache_data(ttl=60)
def fetch_data(symbols, interval, period):
    tickers = [s + ".NS" for s in symbols]
    return yf.download(tickers, period=period, interval=interval, group_by='ticker', progress=False)

with st.spinner("Loading NSE 200 Market Data..."):
    data_5m = fetch_data(stocks, "5m", "5d")

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Pullback_Scan')
    return output.getvalue()

# =============================
# TABS
# =============================
tab1, tab2 = st.tabs(["🚀 LIVE PULLBACK SCANNER", "📊 FULL DAY BACKTEST"])

# -----------------------------
# TAB 1: LIVE PULLBACK SCANNER
# -----------------------------
with tab1:
    if st.button("RUN LIVE SCAN"):
        results = []
        for s in stocks:
            try:
                stock_raw = data_5m.get(s + ".NS")
                if stock_raw is None or stock_raw.empty: continue
                
                df = add_indicators(stock_raw.dropna())
                l = df.iloc[-1]
                dist = abs(l['Close'] - l['EMA20']) / l['EMA20']
                
                # Pullback కండిషన్: ధర EMA20 కి 0.4% లోపు ఉండాలి
                if dist < 0.004:
                    signal = "None"
                    # Buy Pullback: VWAP పైన ఉండి గ్రీన్ క్యాండిల్ అయితే
                    if l['Close'] > l['VWAP'] and l['Close'] > l['Open']:
                        signal = "BUY PULLBACK 🟢"
                    # Sell Pullback: VWAP కింద ఉండి రెడ్ క్యాండిల్ అయితే
                    elif l['Close'] < l['VWAP'] and l['Close'] < l['Open']:
                        signal = "SELL PULLBACK 🔴"
                    
                    if signal != "None":
                        entry = round(l['Close'], 2)
                        atr = l['ATR']
                        results.append({
                            "TIME": df.index[-1].astimezone(IST).strftime('%H:%M'),
                            "STOCK": s, "SIGNAL": signal,
                            "BIG PLAYER": "🔥 YES" if l['Volume'] > (l['VolAvg'] * 2.5) else "-",
                            "ENTRY": entry,
                            "SL": round(entry - (atr*1.5) if "BUY" in signal else entry + (atr*1.5), 2),
                            "TARGET": round(entry + (atr*3) if "BUY" in signal else entry - (atr*3), 2)
                        })
            except: continue
            
        if results:
            res_df = pd.DataFrame(results)
            st.table(res_df)
            st.download_button("📥 Excel Download", data=to_excel(res_df), file_name="Live_Pullback.xlsx")
        else: st.info("No Pullback signals found in NSE 200 right now.")

# -----------------------------
# TAB 2: BACKTEST (PULLBACK & REVERSAL)
# -----------------------------
with tab2:
    bt_date = st.date_input("Analysis Date", value=now.date() - timedelta(days=1))
    if st.button("EXECUTE BACKTEST"):
        bt_logs = []
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
                            # ట్రెండ్ రివర్సల్ లేదా 45 నిమిషాల గ్యాప్ ఉంటేనే చూపించు
                            if curr_sig != last_action or (last_time and (curr_time - last_time) > timedelta(minutes=45)):
                                entry = round(row['Close'], 2)
                                bt_logs.append({
                                    "TIME": curr_time.strftime('%H:%M'),
                                    "STOCK": s, "ACTION": curr_sig,
                                    "BIG PLAYER": "🔥" if row['Volume'] > row['VolAvg']*2.5 else "-",
                                    "ENTRY": entry,
                                    "SL": round(entry - (row['ATR']*1.5) if "BUY" in curr_sig else entry + (row['ATR']*1.5), 2),
                                    "TGT": round(entry + (row['ATR']*3) if "BUY" in curr_sig else entry - (row['ATR']*3), 2)
                                })
                                last_action, last_time = curr_sig, curr_time
            except: continue
            
        if bt_logs:
            st.dataframe(pd.DataFrame(bt_logs), use_container_width=True)
        else: st.warning("No Pullback signals found for the selected date.")
