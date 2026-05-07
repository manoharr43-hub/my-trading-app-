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
st.set_page_config(page_title="🚀 NSE AI QUANT PRO V6.1", layout="wide")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

# UI Styling
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1f2937; padding: 15px; border-radius: 10px; border: 1px solid #374151; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 NSE AI QUANT PRO - V6.1 (Exhaustion Filter)")
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
    
    df['Date_Only'] = df.index.date
    df['PV'] = df['Close'] * df['Volume']
    df['VWAP'] = df.groupby('Date_Only')['PV'].cumsum() / df.groupby('Date_Only')['Volume'].cumsum()
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-9))))
    
    # ADX Calculation
    tr = pd.concat([df['High']-df['Low'], (df['High']-df['Close'].shift()).abs(), (df['Low']-df['Close'].shift()).abs()], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()
    plus_dm = df['High'].diff().where(lambda x: (x > 0) & (x > df['Low'].diff().abs()), 0)
    minus_dm = df['Low'].diff().abs().where(lambda x: (x > 0) & (x > df['High'].diff()), 0)
    plus_di = 100 * (plus_dm.rolling(14).mean() / (df['ATR'] + 1e-9))
    minus_di = 100 * (minus_dm.rolling(14).mean() / (df['ATR'] + 1e-9))
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di + 1e-9)
    df['ADX'] = dx.rolling(14).mean()
    
    df['VolAvg'] = df['Volume'].rolling(20).mean()
    df['RVOL'] = df['Volume'] / (df['VolAvg'] + 1e-9)
    
    # Wick & Body Analysis
    df['High20'] = df['High'].rolling(window=20).max()
    df['Low20'] = df['Low'].rolling(window=20).min()
    df['Range_Width'] = (df['High20'] - df['Low20']) / df['Low20'] * 100
    df['Candle_Range'] = df['High'] - df['Low']
    df['Upper_Wick'] = df['High'] - df[['Open', 'Close']].max(axis=1)
    
    return df

# ==========================================
# 4. DATA LOADER
# ==========================================
@st.cache_data(ttl=60)
def fetch_all_data():
    tickers = [s + ".NS" for s in stocks] + ["^NSEI"]
    return yf.download(tickers, period="5d", interval="5m", group_by="ticker", progress=False, threads=True)

all_data = fetch_all_data()

# ==========================================
# 5. SCANNER LOGIC (With Exhaustion Prevention)
# ==========================================
def scan_stock(s):
    try:
        ticker = s + ".NS"
        df = add_indicators(all_data[ticker].dropna())
        nifty = all_data["^NSEI"].dropna().iloc[-1]
        nifty_trend = "UP" if nifty['Close'] > nifty['Open'] else "DOWN"
        
        last = df.iloc[-1]
        prev = df.iloc[-2]
        
        # 1. Exhaustion Filter (క్యాండిల్ మరీ పెద్దదిగా ఉండకూడదు)
        is_not_exhausted = last['Candle_Range'] < (last['ATR'] * 2.0)
        
        # 2. Distance from EMA Filter (సగటుకు మరీ దూరంగా ఉండకూడదు)
        ema_dist = (last['Close'] - last['EMA20']) / last['EMA20'] * 100
        is_near_ema = ema_dist < 1.1 # 1.1% లోపు దూరం ఉండాలి
        
        # 3. Quality Checks
        is_strong_adx = last['ADX'] > 25
        is_clean_wick = last['Upper_Wick'] < (last['Candle_Range'] * 0.25)
        
        signal, reason = None, ""
        
        if nifty_trend == "UP" and last['Close'] > last['VWAP'] and last['RSI'] > 55 and is_strong_adx:
            if is_not_exhausted and is_near_ema and is_clean_wick:
                if prev['Range_Width'] < 0.8 and last['Close'] > prev['High20']:
                    signal, reason = "BUY", "Healthy Box Breakout ✅"
                elif last['RVOL'] > 2.0:
                    signal, reason = "BUY", "Sustainable Volume Move ⚡"

        if signal:
            sl_pts = float(last['ATR'] * 1.5)
            return {
                "STOCK": s, "SIGNAL": signal, "PRICE": round(last['Close'], 2), "REASON": reason,
                "ADX": round(last['ADX'], 2), "RVOL": round(last['RVOL'], 2), "EMA_DIST": f"{round(ema_dist, 2)}%",
                "SL": round(last['Close'] - sl_pts, 2), "TGT": round(last['Close'] + sl_pts*2.5, 2),
                "TIME": last.name.astimezone(IST).strftime('%H:%M')
            }
    except: return None

# ==========================================
# 6. UI & DOWNLOADS
# ==========================================
tab1, tab2 = st.tabs(["🔴 LIVE SCANNER", "📊 BACKTEST"])

with tab1:
    if st.button("🚀 START SCANNING (V6.1)"):
        with st.spinner("Analyzing Market for Sustainable Moves..."):
            with ThreadPoolExecutor(max_workers=20) as executor:
                res = [r for r in list(executor.map(scan_stock, stocks)) if r]
            
            if res:
                df_res = pd.DataFrame(res)
                st.dataframe(df_res, use_container_width=True)
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_res.to_excel(writer, index=False, sheet_name='Live_Signals')
                st.download_button("📥 Download Live Signals", output.getvalue(), f"Signals_{now.strftime('%H%M')}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            else: st.info("No healthy breakouts found. Avoid chasing big moves!")

with tab2:
    if st.button("📊 RUN V6.1 BACKTEST"):
        all_bt = []
        with st.spinner("Backtesting..."):
            for s in stocks:
                try:
                    df = add_indicators(all_data[s + ".NS"].dropna())
                    for i in range(30, len(df)-10):
                        row = df.iloc[i]
                        prev_row = df.iloc[i-1]
                        ema_d = (row['Close'] - row['EMA20']) / row['EMA20'] * 100
                        
                        if row['ADX'] > 25 and row['RVOL'] > 1.5 and row['Close'] > row['VWAP'] and ema_d < 1.1 and row['Candle_Range'] < (row['ATR'] * 2.0):
                            entry_p = row['Close']
                            sl, tp = entry_p - (row['ATR']*1.5), entry_p + (row['ATR']*2.5)
                            res_bt, exit_t = "OPEN", None
                            for j in range(i+1, min(i+60, len(df))):
                                next_r = df.iloc[j]
                                if next_r['Low'] <= sl: res_bt, exit_t = "LOSS", next_r.name; break
                                if next_r['High'] >= tp: res_bt, exit_t = "PROFIT", next_r.name; break
                            if res_bt != "OPEN":
                                all_bt.append({"Stock": s, "Date": row.name.strftime('%Y-%m-%d'), "Result": res_bt, "EMA_Dist": round(ema_d, 2), "Duration": int((exit_t - row.name).total_seconds() / 60)})
                except: continue
        if all_bt:
            st.dataframe(pd.DataFrame(all_bt), use_container_width=True)
            bt_out = io.BytesIO()
            with pd.ExcelWriter(bt_out, engine='xlsxwriter') as writer:
                pd.DataFrame(all_bt).to_excel(writer, index=False, sheet_name='Backtest')
            st.download_button("📥 Download Backtest Report", bt_out.getvalue(), "Backtest_V6_1.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
