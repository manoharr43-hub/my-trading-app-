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
st.set_page_config(page_title="🚀 NSE AI QUANT PRO V6.0", layout="wide")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

# UI Styling
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1f2937; padding: 15px; border-radius: 10px; border: 1px solid #374151; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 NSE AI QUANT PRO - V6.0 (Advanced Filtering)")
st.subheader(f"📅 {now.strftime('%d-%b-%Y')} | 🕒 {now.strftime('%H:%M:%S')} IST")

# ==========================================
# 2. NSE 200 STOCKS LIST
# ==========================================
stocks = [
    "ABB", "ACC", "AUBANK", "ABBOTINDIA", "ADANIENSOL", "ADANIENT", "ADANIGREEN", "ADANIPORTS", "ADANIPOWER", "ATGL", 
    "ABCAPITAL", "ABFRL", "AEGISCHEM", "AIAENG", "AJANTPHARM", "APLLTD", "ALKEM", "ALKYLAMINE", "AMBUJACEM", "APOLLOHOSP", 
    "APOLLOTYRE", "ASHOKLEY", "ASIANPAINT", "ASTERDM", "ASTRAL", "AUROPHARMA", "AVANTIFEED", "AXISBANK", "BAJAJ-AUTO", "BAJFINANCE", 
    "BAJAJFINSV", "BAJAJHLDNG", "BALKRISIND", "BALRAMCHIN", "BANDHANBNK", "BANKBARODA", "BANKINDIA", "MAHABANK", "BATAINDIA", "BEL", 
    "BERGEPAINT", "BHARATFORG", "BHEL", "BPCL", "BHARTIARTL", "BIOCON", "BIRLACORPN", "BSOFT", "BLUEDART", "BLUESTARCO", 
    "BOSCHLTD", "BRITANNIA", "CANBK", "CGPOWER", "CHAMBLFERT", "CHOLAFIN", "CHOLAHLDNG", "CIPLA", "COALINDIA", "COFORGE", 
    "COLPAL", "CONCOR", "COROMANDEL", "CROMPTON", "CUMMINSIND", "CYIENT", "DABUR", "DALBHARAT", "DEEPAKNTR", "DELHIVERY", 
    "DIVISLAB", "DIXON", "DLF", "DRREDDY", "EICHERMOT", "EIDPARRY", "EIHOTEL", "ELGIEQUIP", "EMAMILTD", "ENDURANCE", 
    "ENGINERSIN", "ESCORTS", "EXIDEIND", "FEDERALBNK", "FORTIS", "GAIL", "GLENMARK", "GMRINFRA", "GODREJCP", "GODREJPROP", 
    "GRANULES", "GRASIM", "GUJGASLTD", "GNFC", "GSFC", "HAL", "HAPPSTMNDS", "HAVELLS", "HCLTECH", "HDFCBANK", "HDFCLIFE", 
    "HDFCAMC", "HEG", "HEROMOTOCO", "HINDALCO", "HINDCOPPER", "HINDPETRO", "HINDUNILVR", "HINDZINC", "HUDCO", "ICICIBANK", 
    "ICICIGI", "ICICIPRULI", "IDFCFIRSTB", "IEX", "IGL", "INDHOTEL", "INDIACEM", "INDIAMART", "INDIANB", 
    "INDIGO", "INDUSINDBK", "INDUSTOWER", "INFY", "IOC", "IRCTC", "IRFC", "ITC", 
    "JKCEMENT", "JINDALSTEL", "JSWENERGY", "JSWSTEEL", "JUBLFOOD", "KOTAKBANK", "KPITTECH", "L&TFH", "LT", "LTIM", "LTTS", 
    "LICHSGFIN", "LICI", "LUPIN", "M&M", "M&MFIN", "MANAPPURAM", "MARICO", "MARUTI", "MAXHEALTH", "METROPOLIS", 
    "MFSL", "MGL", "MPHASIS", "MRF", "MUTHOOTFIN", "NATIONALUM", "NESTLEIND", "NMDC", "NTPC", "OBEROIRLTY", 
    "ONGC", "PAYTM", "PEL", "PERSISTENT", "PETRONET", "PFC", "PIDILITIND", "PIIND", "PNB", "POLYCAB", 
    "POONAWALLA", "POWERGRID", "PRESTIGE", "PVRINOX", "RECLTD", "RELIANCE", "SAIL", "SBICARD", "SBILIFE", "SBIN", 
    "SHREECEM", "SHRIRAMFIN", "SIEMENS", "SRF", "SUNPHARMA", "SUNTV", "SYNGENE", "TATACOMM", "TATACONSUM", 
    "TATAELXSI", "TATAMOTORS", "TATAPOWER", "TATASTEEL", "TCS", "TECHM", "TITAN", "TORNTPHARM", "TRENT", 
    "TVSMOTOR", "ULTRACEMCO", "UBL", "UPL", "VBL", "VEDL", "VOLTAS", "WIPRO", "YESBANK", "ZEEL", "ZOMATO"
]

# ==========================================
# 3. CORE INDICATORS ENGINE (Enhanced)
# ==========================================
def add_indicators(df):
    df = df.copy()
    if df.empty: return df
    
    # 1. VWAP & EMA
    df['Date_Only'] = df.index.date
    df['PV'] = df['Close'] * df['Volume']
    df['VWAP'] = df.groupby('Date_Only')['PV'].cumsum() / df.groupby('Date_Only')['Volume'].cumsum()
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    
    # 2. RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-9))))
    
    # 3. ADX (Trend Strength)
    plus_dm = df['High'].diff().where(lambda x: (x > 0) & (x > df['Low'].diff().abs()), 0)
    minus_dm = df['Low'].diff().abs().where(lambda x: (x > 0) & (x > df['High'].diff()), 0)
    tr = pd.concat([df['High']-df['Low'], (df['High']-df['Close'].shift()).abs(), (df['Low']-df['Close'].shift()).abs()], axis=1).max(axis=1)
    atr_adx = tr.rolling(14).mean()
    plus_di = 100 * (plus_dm.rolling(14).mean() / (atr_adx + 1e-9))
    minus_di = 100 * (minus_dm.rolling(14).mean() / (atr_adx + 1e-9))
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di + 1e-9)
    df['ADX'] = dx.rolling(14).mean()
    
    # 4. Volatility & RVOL
    df['ATR'] = tr.rolling(14).mean()
    df['VolAvg'] = df['Volume'].rolling(20).mean()
    df['RVOL'] = df['Volume'] / (df['VolAvg'] + 1e-9)
    
    # 5. Consolidation & Wick Analysis
    df['High20'] = df['High'].rolling(window=20).max()
    df['Low20'] = df['Low'].rolling(window=20).min()
    df['Range_Width'] = (df['High20'] - df['Low20']) / df['Low20'] * 100
    
    # Candle Wick Calculation
    df['Candle_Range'] = df['High'] - df['Low']
    df['Upper_Wick'] = df['High'] - df[['Open', 'Close']].max(axis=1)
    df['Lower_Wick'] = df[['Open', 'Close']].min(axis=1) - df['Low']
    
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
# 5. SCANNER LOGIC (With Wick & ADX Filters)
# ==========================================
def scan_stock(s):
    try:
        ticker = s + ".NS"
        df = add_indicators(all_data[ticker].dropna())
        nifty = all_data["^NSEI"].dropna().iloc[-1]
        nifty_trend = "UP" if nifty['Close'] > nifty['Open'] else "DOWN"
        
        last = df.iloc[-1]
        prev = df.iloc[-2]
        
        # New Filters
        is_strong_adx = last['ADX'] > 25
        is_clean_buy_candle = last['Upper_Wick'] < (last['Candle_Range'] * 0.25) # Max 25% wick
        is_clean_sell_candle = last['Lower_Wick'] < (last['Candle_Range'] * 0.25)
        is_cons = prev['Range_Width'] < 0.8
        
        signal, reason = None, ""
        
        # BUY Logic
        if nifty_trend == "UP" and last['Close'] > last['VWAP'] and last['RSI'] > 55 and is_strong_adx:
            if is_clean_buy_candle:
                if is_cons and last['Close'] > prev['High20'] and last['RVOL'] > 1.5:
                    signal, reason = "BUY", "Strong Box Breakout 🚀"
                elif last['RVOL'] > 2.0:
                    signal, reason = "BUY", "High Volume Trend ⚡"
        
        # SELL Logic
        elif nifty_trend == "DOWN" and last['Close'] < last['VWAP'] and last['RSI'] < 45 and is_strong_adx:
            if is_clean_sell_candle:
                if is_cons and last['Close'] < prev['Low20'] and last['RVOL'] > 1.5:
                    signal, reason = "SELL", "Box Breakdown 📉"
                elif last['RVOL'] > 2.0:
                    signal, reason = "SELL", "Big Exit 🔴"

        if signal:
            sl_pts = float(last['ATR'] * 1.5)
            return {
                "STOCK": s, "SIGNAL": signal, "PRICE": round(last['Close'], 2), "REASON": reason,
                "ADX": round(last['ADX'], 2), "RVOL": round(last['RVOL'], 2),
                "SL": round(last['Close'] - sl_pts if signal=="BUY" else last['Close'] + sl_pts, 2),
                "TGT": round(last['Close'] + sl_pts*2.5 if signal=="BUY" else last['Close'] - sl_pts*2.5, 2),
                "TIME": last.name.astimezone(IST).strftime('%H:%M')
            }
    except: return None

# ==========================================
# 6. UI & EXCEL DOWNLOAD
# ==========================================
tab1, tab2 = st.tabs(["🔴 LIVE SCANNER", "📊 BACKTEST"])

with tab1:
    if st.button("🚀 START SCANNING (V6.0)"):
        with st.spinner("Analyzing Market Dynamics..."):
            with ThreadPoolExecutor(max_workers=20) as executor:
                res = [r for r in list(executor.map(scan_stock, stocks)) if r]
            
            if res:
                df_res = pd.DataFrame(res)
                st.dataframe(df_res, use_container_width=True)
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_res.to_excel(writer, index=False, sheet_name='Live_Signals')
                st.download_button("📥 Download Live Signals", output.getvalue(), f"Signals_{now.strftime('%H%M')}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            else: st.info("No high-quality signals meeting Wick & ADX criteria.")

with tab2:
    if st.button("📊 RUN V6.0 BACKTEST"):
        all_bt = []
        with st.spinner("Backtesting with Advanced Filters..."):
            for s in stocks:
                try:
                    df = add_indicators(all_data[s + ".NS"].dropna())
                    for i in range(30, len(df)-10):
                        row = df.iloc[i]
                        # Apply V6.0 Logic for Backtest
                        if row['ADX'] > 25 and row['RVOL'] > 1.5 and row['RSI'] > 55 and row['Close'] > row['VWAP']:
                            # Simplified backtest exit check
                            entry_p = row['Close']
                            sl = entry_p - (row['ATR']*1.5)
                            tp = entry_p + (row['ATR']*2.5)
                            
                            res_bt, exit_t = "OPEN", None
                            for j in range(i+1, min(i+60, len(df))):
                                next_r = df.iloc[j]
                                if next_r['Low'] <= sl: res_bt, exit_t = "LOSS", next_r.name; break
                                if next_r['High'] >= tp: res_bt, exit_t = "PROFIT", next_r.name; break
                            
                            if res_bt != "OPEN":
                                all_bt.append({
                                    "Stock": s, "Date": row.name.strftime('%Y-%m-%d'), "Signal": "BUY",
                                    "ADX": round(row['ADX'], 2), "RVOL": round(row['RVOL'], 2),
                                    "Result": res_bt, "Duration": int((exit_t - row.name).total_seconds() / 60)
                                })
                except: continue
        
        if all_bt:
            df_bt = pd.DataFrame(all_bt)
            st.dataframe(df_bt, use_container_width=True)
            bt_out = io.BytesIO()
            with pd.ExcelWriter(bt_out, engine='xlsxwriter') as writer:
                df_bt.to_excel(writer, index=False, sheet_name='Backtest')
            st.download_button("📥 Download V6.0 Backtest Report", bt_out.getvalue(), "Backtest_V6.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else: st.warning("No trades met the V6.0 criteria.")
