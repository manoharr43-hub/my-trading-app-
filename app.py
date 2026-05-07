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
st.set_page_config(page_title="🚀 NSE AI QUANT PRO V6.2", layout="wide")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

# UI Styling
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1f2937; padding: 15px; border-radius: 10px; border: 1px solid #374151; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 NSE AI QUANT PRO - V6.2 (Full Day Tracker)")
st.subheader(f"📅 {now.strftime('%d-%b-%Y')} | 🕒 {now.strftime('%H:%M:%S')} IST")

# ==========================================
# 2. NSE 200 STOCKS LIST
# ==========================================
stocks = [
    "ABB", "ACC", "AUBANK", "ADANIENSOL", "ADANIENT", "ADANIGREEN", "ADANIPORTS", "ADANIPOWER", "ATGL", 
    "ABCAPITAL", "ABFRL", "ALKEM", "AMBUJACEM", "APOLLOHOSP", "APOLLOTYRE", "ASHOKLEY", "ASIANPAINT", "ASTRAL", 
    "AUROPHARMA", "AXISBANK", "BAJAJ-AUTO", "BAJFINANCE", "BAJAJFINSV", "BAJAJHLDNG", "BALKRISIND", "BANDHANBNK", 
    "BANKBARODA", "BEL", "BERGEPAINT", "BHARATFORG", "BHEL", "BPCL", "BHARTIARTL", "BIOCON", "BOSCHLTD", 
    "BRITANNIA", "CANBK", "CGPOWER", "CHOLAFIN", "CIPLA", "COALINDIA", "COFORGE", "COLPAL", "CONCOR", 
    "COROMANDEL", "CROMPTON", "CUMMINSIND", "CYIENT", "DABUR", "DALBHARAT", "DEEPAKNTR", "DELHIVERY", 
    "DIVISLAB", "DIXON", "DLF", "DRREDDY", "EICHERMOT", "ESCORTS", "EXIDEIND", "FEDERALBNK", "FORTIS", 
    "GAIL", "GLENMARK", "GMRINFRA", "GODREJCP", "GODREJPROP", "GRASIM", "GUJGASLTD", "HAL", "HAVELLS", 
    "HCLTECH", "HDFCBANK", "HDFCLIFE", "HEROMOTOCO", "HINDALCO", "HINDCOPPER", "HINDPETRO", "HINDUNILVR", 
    "ICICIBANK", "IDFCFIRSTB", "IEX", "IGL", "INDHOTEL", "INDIGO", "INDUSINDBK", "INDUSTOWER", "INFY", 
    "IOC", "IRCTC", "IRFC", "ITC", "JINDALSTEL", "JSWENERGY", "JSWSTEEL", "JUBLFOOD", "KOTAKBANK", 
    "KPITTECH", "LT", "LTIM", "LTTS", "LICI", "LUPIN", "M&M", "M&MFIN", "MARICO", "MARUTI", "MAXHEALTH", 
    "METROPOLIS", "MFSL", "MGL", "MPHASIS", "MRF", "MUTHOOTFIN", "NATIONALUM", "NESTLEIND", "NMDC", 
    "NTPC", "OBEROIRLTY", "ONGC", "PAYTM", "PERSISTENT", "PETRONET", "PFC", "PIDILITIND", "PIIND", "PNB", 
    "POLYCAB", "POONAWALLA", "POWERGRID", "PRESTIGE", "PVRINOX", "RECLTD", "RELIANCE", "SAIL", "SBICARD", 
    "SBILIFE", "SBIN", "SIEMENS", "SRF", "SUNPHARMA", "SUNTV", "SYNGENE", "TATACOMM", "TATACONSUM", 
    "TATAELXSI", "TATAMOTORS", "TATAPOWER", "TATASTEEL", "TCS", "TECHM", "TITAN", "TORNTPHARM", "TRENT", 
    "TVSMOTOR", "ULTRACEMCO", "UPL", "VBL", "VEDL", "VOLTAS", "WIPRO", "YESBANK", "ZEEL", "ZOMATO"
]

# ==========================================
# 3. CORE INDICATORS ENGINE
# ==========================================
def add_indicators(df):
    df = df.copy()
    if df.empty: return df
    
    # VWAP & EMA
    df['Date_Only'] = df.index.date
    df['PV'] = df['Close'] * df['Volume']
    df['VWAP'] = df.groupby('Date_Only')['PV'].cumsum() / df.groupby('Date_Only')['Volume'].cumsum()
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    
    # RSI & ADX
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-9))))
    
    tr = pd.concat([df['High']-df['Low'], (df['High']-df['Close'].shift()).abs(), (df['Low']-df['Close'].shift()).abs()], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()
    plus_dm = df['High'].diff().where(lambda x: (x > 0) & (x > df['Low'].diff().abs()), 0)
    minus_dm = df['Low'].diff().abs().where(lambda x: (x > 0) & (x > df['High'].diff()), 0)
    df['ADX'] = (100 * (plus_dm.rolling(14).mean() - minus_dm.rolling(14).mean()).abs() / (plus_dm.rolling(14).mean() + minus_dm.rolling(14).mean() + 1e-9)).rolling(14).mean()
    
    # RVOL & Body
    df['VolAvg'] = df['Volume'].rolling(20).mean()
    df['RVOL'] = df['Volume'] / (df['VolAvg'] + 1e-9)
    df['High20'] = df['High'].rolling(window=20).max()
    df['Low20'] = df['Low'].rolling(window=20).min()
    df['Range_Width'] = (df['High20'] - df['Low20']) / df['Low20'] * 100
    df['Candle_Range'] = df['High'] - df['Low']
    df['Upper_Wick'] = df['High'] - df[['Open', 'Close']].max(axis=1)
    
    return df

@st.cache_data(ttl=60)
def fetch_all_data():
    tickers = [s + ".NS" for s in stocks] + ["^NSEI"]
    return yf.download(tickers, period="1d", interval="5m", group_by="ticker", progress=False, threads=True)

all_data = fetch_all_data()

# ==========================================
# 4. FULL DAY SIGNAL TRACKER ENGINE
# ==========================================
def track_daily_signals(s):
    try:
        ticker = s + ".NS"
        df = add_indicators(all_data[ticker].dropna())
        nifty = all_data["^NSEI"].dropna()
        
        signals = []
        # ఉదయం నుండి ప్రతి క్యాండిల్‌ను చెక్ చేయడం
        for i in range(25, len(df)):
            row = df.iloc[i]
            prev = df.iloc[i-1]
            
            # Filters
            ema_dist = (row['Close'] - row['EMA20']) / row['EMA20'] * 100
            is_healthy = row['Candle_Range'] < (row['ATR'] * 2.1) and ema_dist < 1.1
            is_clean = row['Upper_Wick'] < (row['Candle_Range'] * 0.25)
            
            # Nifty trend at that specific time
            nifty_at_time = nifty.reindex(df.index, method='ffill').iloc[i]
            n_trend = "UP" if nifty_at_time['Close'] > nifty_at_time['Open'] else "DOWN"
            
            if n_trend == "UP" and row['Close'] > row['VWAP'] and row['RSI'] > 55:
                if is_healthy and is_clean:
                    if prev['Range_Width'] < 0.8 and row['Close'] > prev['High20'] and row['RVOL'] > 1.2:
                        signals.append({
                            "TIME": row.name.astimezone(IST).strftime('%H:%M'),
                            "STOCK": s, "SIGNAL": "BUY", "PRICE": round(row['Close'], 2),
                            "REASON": "Healthy Box Breakout", "RVOL": round(row['RVOL'], 2),
                            "EMA_DIST": f"{round(ema_dist, 2)}%"
                        })
                    elif row['RVOL'] > 2.0:
                        signals.append({
                            "TIME": row.name.astimezone(IST).strftime('%H:%M'),
                            "STOCK": s, "SIGNAL": "BUY", "PRICE": round(row['Close'], 2),
                            "REASON": "Sustainable Volume Move", "RVOL": round(row['RVOL'], 2),
                            "EMA_DIST": f"{round(ema_dist, 2)}%"
                        })
        return signals
    except: return []

# ==========================================
# 5. UI INTERFACE
# ==========================================
tab1, tab2 = st.tabs(["🔍 FULL DAY SIGNAL TRACKER", "📊 HISTORICAL BACKTEST"])

with tab1:
    if st.button("🚀 SCAN ALL SIGNALS FROM MORNING"):
        with st.spinner("ఉదయం నుండి వచ్చిన అన్ని క్వాలిటీ సిగ్నల్స్ వెతుకుతున్నాను..."):
            with ThreadPoolExecutor(max_workers=20) as executor:
                all_results = list(executor.map(track_daily_signals, stocks))
            
            # Combine all signal lists
            final_signals = [sig for sublist in all_results for sig in sublist]
            
            if final_signals:
                df_final = pd.DataFrame(final_signals).sort_values(by="TIME", ascending=False)
                st.success(f"మొత్తం {len(df_final)} సిగ్నల్స్ గుర్తించబడ్డాయి.")
                st.dataframe(df_final, use_container_width=True)
                
                # Excel Export
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_final.to_excel(writer, index=False, sheet_name='Today_Signals')
                st.download_button("📥 Download Today's Signal History", output.getvalue(), f"FullDay_{now.strftime('%d%m')}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            else:
                st.info("ఈరోజు ఇప్పటివరకు ఎటువంటి క్వాలిటీ సిగ్నల్స్ నమోదు కాలేదు.")

with tab2:
    st.write("గత 5 రోజుల డేటాను అనలైజ్ చేయడానికి పాత బ్యాక్‌టెస్ట్ లాజిక్ ఇక్కడ వాడవచ్చు.")
    if st.button("📊 RUN 5-DAY BACKTEST"):
        # (పాత బ్యాక్‌టెస్ట్ కోడ్ ఇక్కడ కొనసాగుతుంది...)
        st.write("బ్యాక్‌టెస్ట్ ప్రాసెసింగ్...")
