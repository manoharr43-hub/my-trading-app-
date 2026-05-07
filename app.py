import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
from concurrent.futures import ThreadPoolExecutor
import io

# ==========================================
# 1. CONFIG & TIMEZONE SETUP
# ==========================================
st.set_page_config(page_title="🚀 NSE AI QUANT PRO V6.7", layout="wide")
IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

# UI Styling for Top Box
st.markdown("""
    <style>
    .nifty-box { padding: 20px; border-radius: 10px; border: 1px solid #4B5563; text-align: center; font-size: 22px; font-weight: bold; margin-bottom: 20px; }
    .pos-trend { background-color: #064e3b; color: #10b981; border: 2px solid #10b981; }
    .neg-trend { background-color: #450a0a; color: #f87171; border: 2px solid #f87171; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. FULL NSE 200 STOCKS LIST
# ==========================================
stocks = [
    "ABB", "ACC", "AUBANK", "ADANIENSOL", "ADANIENT", "ADANIGREEN", "ADANIPORTS", "ADANIPOWER", "ATGL", "ABCAPITAL", 
    "ABFRL", "ALKEM", "AMBUJACEM", "APOLLOHOSP", "APOLLOTYRE", "ASHOKLEY", "ASIANPAINT", "ASTRAL", "AUROPHARMA", 
    "AXISBANK", "BAJAJ-AUTO", "BAJFINANCE", "BAJAJFINSV", "BAJAJHLDNG", "BALKRISIND", "BANDHANBNK", "BANKBARODA", 
    "BANKINDIA", "BATAINDIA", "BEL", "BERGEPAINT", "BHARATFORG", "BHEL", "BPCL", "BHARTIARTL", "BIOCON", 
    "BOSCHLTD", "BRITANNIA", "CANBK", "CGPOWER", "CHOLAFIN", "CIPLA", "COALINDIA", "COFORGE", "COLPAL", 
    "CONCOR", "COROMANDEL", "CROMPTON", "CUMMINSIND", "CYIENT", "DABUR", "DALBHARAT", "DEEPAKNTR", "DELHIVERY", 
    "DIVISLAB", "DIXON", "DLF", "DRREDDY", "EICHERMOT", "ESCORTS", "EXIDEIND", "FEDERALBNK", "FORTIS", "GAIL", 
    "GLENMARK", "GMRINFRA", "GODREJCP", "GODREJPROP", "GRASIM", "GUJGASLTD", "HAL", "HAVELLS", "HCLTECH", 
    "HDFCBANK", "HDFCLIFE", "HEROMOTOCO", "HINDALCO", "HINDCOPPER", "HINDPETRO", "HINDUNILVR", "ICICIBANK", 
    "IDFCFIRSTB", "IEX", "IGL", "INDHOTEL", "INDIGO", "INDUSINDBK", "INDUSTOWER", "INFY", "IOC", "IRCTC", 
    "IRFC", "ITC", "JINDALSTEL", "JSWENERGY", "JSWSTEEL", "JUBLFOOD", "KOTAKBANK", "KPITTECH", "LT", "LTIM", 
    "LTTS", "LICI", "LUPIN", "M&M", "M&MFIN", "MARICO", "MARUTI", "MAXHEALTH", "METROPOLIS", "MFSL", "MGL", 
    "MPHASIS", "MRF", "MUTHOOTFIN", "NATIONALUM", "NESTLEIND", "NMDC", "NTPC", "OBEROIRLTY", "ONGC", "PAYTM", 
    "PERSISTENT", "PETRONET", "PFC", "PIDILITIND", "PIIND", "PNB", "POLYCAB", "POONAWALLA", "POWERGRID", 
    "PRESTIGE", "PVRINOX", "RECLTD", "RELIANCE", "SAIL", "SBICARD", "SBILIFE", "SBIN", "SIEMENS", "SRF", 
    "SUNPHARMA", "SUNTV", "SYNGENE", "TATACOMM", "TATACONSUM", "TATAELXSI", "TATAMOTORS", "TATAPOWER", 
    "TATASTEEL", "TCS", "TECHM", "TITAN", "TORNTPHARM", "TRENT", "TVSMOTOR", "ULTRACEMCO", "UPL", "VBL", 
    "VEDL", "VOLTAS", "WIPRO", "YESBANK", "ZEEL", "ZOMATO", "ZYDUSLIFE", "ABBOTINDIA", "ALKYLAMINE", 
    "APLLTD", "APLAPOLLO", "AWHCL", "BAJAJELEC", "BERGEPAINT", "BIRLACORPN", "BLS", "BLUESTARCO", "BSOFT", 
    "CAMPUS", "CASTROLIND", "CEATLTD", "CENTURYPLY", "CESC", "CHAMBLFERT", "CHOLAHLDNG", "CIEINDIA", 
    "CLEAN", "COCHINSHIP", "CREDITACC", "DATAPATTNS", "EASEMYTRIP", "EIDPARRY", "EIHOTEL", "ELGIEQUIP", 
    "EMAMILTD", "ENDURANCE", "ENGINERSIN", "EQUITASBNK", "ERIS", "ESAFSFB", "FINEORG", "FINPIPE", 
    "FSL", "GABRIEL", "GLS", "GNFC", "GODREJIND", "GRINFRA", "GSFC", "HEG", "HGINFRA", "HINDZINC", 
    "HUDCO", "IBULHSGFIN", "IDBI", "IDFC", "IIFL", "IRB", "ITI", "JBCHEPHARM", "JKCEMENT", "JKPAPER", 
    "JSL", "KALYANKJIL", "KEI", "KNRCON", "KRBL", "L&TFH", "LATENTVIEW", "LAURUSLABS", "LXCHEM", 
    "MAHLOG", "MANAPPURAM", "MAPMYINDIA", "MASTEK", "MEDPLUS", " METROBRAND", "MOTILALOFS", "MTARTECH", 
    "NAZARA", "NHPC", "NLCINDIA", "OBEROIRLTY", "OIL", "PATELENG", "PHOENIXLTD", "PPLPHARMA", "PRINCEPIPE", 
    "PRIVISCL", "QUESS", "RADICO", "RAIN", "RAJESHEXPO", "RATNAMANI", "RITES", "RVNL", "SJVN", "SKFINDIA", 
    "SONACOMS", "STARHEALTH", "SUPREMEIND", "SUZLON", "SWANENERGY", "TATAINVEST", "TEAMLEASE", "TEJASNET", 
    "TRITURBINE", "TRIVENI", "UCOBANK", "UNIONBANK", "VIPIND", "WHIRLPOOL", "ZENSARTECH"
]

# ==========================================
# 3. INDICATORS ENGINE
# ==========================================
def add_indicators(df):
    df = df.copy()
    if df.empty: return df
    df['Date_Only'] = df.index.date
    df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['PV'] = df['Close'] * df['Volume']
    df['VWAP'] = df.groupby('Date_Only')['PV'].cumsum() / df.groupby('Date_Only')['Volume'].cumsum()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-9))))
    tr = pd.concat([df['High']-df['Low'], (df['High']-df['Close'].shift()).abs(), (df['Low']-df['Close'].shift()).abs()], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()
    df['VolAvg'] = df['Volume'].rolling(20).mean()
    df['RVOL'] = df['Volume'] / (df['VolAvg'] + 1e-9)
    df['Range_Width'] = (df['High'].rolling(20).max() - df['Low'].rolling(20).min()) / df['Low'].rolling(20).min() * 100
    return df

@st.cache_data(ttl=60)
def fetch_all_data():
    tickers = [s + ".NS" for s in stocks] + ["^NSEI"]
    data_5m = yf.download(tickers, period="5d", interval="5m", group_by="ticker", progress=False, threads=True)
    data_1h = yf.download("^NSEI", period="5d", interval="1h", progress=False)
    return data_5m, data_1h

# ==========================================
# 4. SCAN LOGIC
# ==========================================
def scan_stock(s, d5, nifty_5m, n_direction_1h):
    try:
        df = add_indicators(d5[s + ".NS"].dropna())
        if df.empty: return None
        
        for i in range(25, len(df)):
            row = df.iloc[i]
            prev = df.iloc[i-1]
            n_row_5m = nifty_5m.reindex(df.index, method='ffill').iloc[i]
            
            ema_dist = (row['Close'] - row['EMA20']) / row['EMA20'] * 100
            is_healthy = abs(ema_dist) < 0.9 and (row['High'] - row['Low']) < (row['ATR'] * 1.9)

            # BUY Logic
            if n_direction_1h == "POSITIVE" and n_row_5m['Close'] > n_row_5m['EMA20']:
                if row['Close'] > row['VWAP'] and row['EMA9'] > row['EMA21'] and row['RSI'] > 50 and is_healthy:
                    if prev['Range_Width'] < 0.45 or row['RVOL'] > 2.0:
                        if row['Close'] > prev['High']:
                            return {"TIME": row.name.astimezone(IST).strftime('%H:%M'), "STOCK": s, "SIGNAL": "BUY", "PRICE": round(row['Close'], 2), "RVOL": round(row['RVOL'], 2), "STATUS": "BOS 🚀"}

            # SELL Logic
            elif n_direction_1h == "NEGATIVE" and n_row_5m['Close'] < n_row_5m['EMA20']:
                if row['Close'] < row['VWAP'] and row['EMA9'] < row['EMA21'] and row['RSI'] < 45 and is_healthy:
                    if prev['Range_Width'] < 0.45 or row['RVOL'] > 2.0:
                        if row['Close'] < prev['Low']:
                            return {"TIME": row.name.astimezone(IST).strftime('%H:%M'), "STOCK": s, "SIGNAL": "SELL", "PRICE": round(row['Close'], 2), "RVOL": round(row['RVOL'], 2), "STATUS": "BOS 📉"}
    except: return None
    return None

# ==========================================
# 5. UI INTERFACE
# ==========================================
d5, d1h = fetch_all_data()
nifty_5m = add_indicators(d5["^NSEI"].dropna())
n_last_1h = d1h['Close'].iloc[-1]
n_ema_1h = d1h['Close'].ewm(span=20, adjust=False).mean().iloc[-1]
n_direction_1h = "POSITIVE" if n_last_1h > n_ema_1h else "NEGATIVE"

# Top Direction Box
box_class = "pos-trend" if n_direction_1h == "POSITIVE" else "neg-trend"
st.markdown(f'<div class="nifty-box {box_class}">NIFTY 50 1-HOUR TREND: {n_direction_1h} {"📈" if n_direction_1h == "POSITIVE" else "📉"}</div>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🔍 LIVE TRACKER (NSE 200)", "📊 BACKTEST REPORT"])

with tab1:
    if st.button("🚀 START FULL SCAN (NSE 200)"):
        with st.spinner("200 స్టాక్స్‌ను విశ్లేషిస్తున్నాను..."):
            with ThreadPoolExecutor(max_workers=25) as executor:
                results = list(executor.map(lambda s: scan_stock(s, d5, nifty_5m, n_direction_1h), stocks))
            
            final_res = [r for r in results if r]
            if final_res:
                df_final = pd.DataFrame(final_res).sort_values(by="TIME", ascending=False)
                st.dataframe(df_final, use_container_width=True)
                # Excel Download
                out = io.BytesIO()
                with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
                    df_final.to_excel(writer, index=False, sheet_name='Today_Signals')
                st.download_button("📥 Download Excel Report", out.getvalue(), f"NSE200_Signals_{now.strftime('%d%m')}.xlsx")
            else:
                st.info("ప్రస్తుత నిఫ్టీ ట్రెండ్‌కు అనుగుణంగా ఎటువంటి బలమైన సిగ్నల్స్ లేవు.")

with tab2:
    st.write("గత 5 రోజుల బ్యాక్‌టెస్ట్ రిపోర్ట్ ఇక్కడ జనరేట్ అవుతుంది.")
    if st.button("📊 RUN BACKTEST"):
        st.write("Backtest processing for 200 stocks... please wait.")
