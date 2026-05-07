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
st.set_page_config(page_title="🚀 NSE AI QUANT PRO V5.0", layout="wide")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

# UI Styling
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1f2937; padding: 15px; border-radius: 10px; border: 1px solid #374151; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 NSE AI QUANT PRO - V5.0 (NSE 200)")
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
    "ICICIGI", "ICICIPRULI", "IDBI", "IDFCFIRSTB", "IEX", "IGL", "INDHOTEL", "INDIACEM", "INDIAMART", "INDIANB", 
    "ISEC", "INDIGO", "INDUSINDBK", "INDUSTOWER", "INFY", "INTELLECT", "IOC", "IRCTC", "IRFC", "ITC", "ITI", 
    "JBCHEPHARM", "JKCEMENT", "JKLAKSHMI", "JINDALSTEL", "JSL", "JSWENERGY", "JSWSTEEL", "JUBLFOOD", "KALYANKJIL", "KEI", 
    "KEC", "KOTAKBANK", "KPITTECH", "KPRMILL", "KRBL", "KSB", "L&TFH", "LT", "LTIM", "LTTS", "LICHSGFIN", "LICI", 
    "LINDEINDIA", "LUPIN", "M&M", "M&MFIN", "MANAPPURAM", "MARICO", "MARUTI", "MAXHEALTH", "MAZDOCK", "METROPOLIS", 
    "MFSL", "MGL", "MOTILALOFS", "MPHASIS", "MRF", "MUTHOOTFIN", "NATCOPHARM", "NATIONALUM", "NAVINFLUOR", "NESTLEIND", 
    "NMDC", "NTPC", "NHPC", "OBEROIRLTY", "ONGC", "OIL", "PAYTM", "OFSS", "PAGEIND", "PEL", "PERSISTENT", "PETRONET", 
    "PFC", "PIDILITIND", "PIIND", "PNB", "POLYCAB", "POONAWALLA", "POWERGRID", "PRAJIND", "PRESTIGE", "PVRINOX", 
    "RAMCOCEM", "RATNAMANI", "RBLBANK", "RECLTD", "RELIANCE", "RVNL", "SAIL", "SBICARD", "SBILIFE", "SBIN", 
    "SHREECEM", "SHRIRAMFIN", "SIEMENS", "SRF", "SUNPHARMA", "SUNTV", "SUPREMEIND", "SUZLON", "SYNGENE", "TATACOMM", 
    "TATACONSUM", "TATAELXSI", "TATAMOTORS", "TATAPOWER", "TATASTEEL", "TCS", "TECHM", "TITAN", "TORNTPHARM", "TORNTPOWER", 
    "TRENT", "TRIDENT", "TIINDIA", "TVSMOTOR", "UCOBANK", "ULTRACEMCO", "UNIONBANK", "UBL", "UPL", "VBL", "VEDL", 
    "VOLTAS", "WHIRLPOOL", "WIPRO", "YESBANK", "ZEEL", "ZENSARTECH", "ZOMATO"
]

# ==========================================
# 3. CORE INDICATORS ENGINE
# ==========================================
def add_indicators(df):
    df = df.copy()
    if df.empty: return df
    
    # Intraday VWAP
    df['Date_Only'] = df.index.date
    df['PV'] = df['Close'] * df['Volume']
    df['VWAP'] = df.groupby('Date_Only')['PV'].cumsum() / df.groupby('Date_Only')['Volume'].cumsum()
    
    # Trend & Momentum
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-9))))
    
    # ATR & RVOL
    tr = pd.concat([df['High']-df['Low'], abs(df['High']-df['Close'].shift()), abs(df['Low']-df['Close'].shift())], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()
    df['VolAvg'] = df['Volume'].rolling(20).mean()
    df['RVOL'] = df['Volume'] / (df['VolAvg'] + 1e-9)
    
    # Consolidation
    df['High20'] = df['High'].rolling(window=20).max()
    df['Low20'] = df['Low'].rolling(window=20).min()
    df['Range_Width'] = (df['High20'] - df['Low20']) / df['Low20'] * 100
    
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
# 5. SCANNER LOGIC
# ==========================================
def scan_stock(s):
    try:
        ticker = s + ".NS"
        df = add_indicators(all_data[ticker].dropna())
        nifty = all_data["^NSEI"].dropna().iloc[-1]
        nifty_trend = "UP" if nifty['Close'] > nifty['Open'] else "DOWN"
        
        last = df.iloc[-1]
        is_cons = last['Range_Width'] < 0.8
        
        signal, reason = None, ""
        # BUY Logic
        if nifty_trend == "UP" and last['Close'] > last['VWAP'] and last['RSI'] > 55:
            if is_cons and last['Close'] > df.iloc[-2]['High20'] and last['RVOL'] > 1.5:
                signal, reason = "BUY", "Consolidation Breakout 🚀"
            elif last['RVOL'] > 2.0:
                signal, reason = "BUY", "Big Player Entry ⚡"
        
        # SELL Logic
        elif nifty_trend == "DOWN" and last['Close'] < last['VWAP'] and last['RSI'] < 45:
            if is_cons and last['Close'] < df.iloc[-2]['Low20'] and last['RVOL'] > 1.5:
                signal, reason = "SELL", "Consolidation Breakdown 📉"
            elif last['RVOL'] > 2.0:
                signal, reason = "SELL", "Big Exit 🔴"

        if signal:
            sl_pts = float(last['ATR'] * 1.5)
            return {
                "STOCK": s, "SIGNAL": signal, "PRICE": round(last['Close'], 2), "REASON": reason,
                "RVOL": round(last['RVOL'], 2), "SL": round(last['Close'] - sl_pts if signal=="BUY" else last['Close'] + sl_pts, 2),
                "TGT": round(last['Close'] + sl_pts*2.5 if signal=="BUY" else last['Close'] - sl_pts*2.5, 2),
                "TIME": last.name.astimezone(IST).strftime('%H:%M')
            }
    except: return None

# ==========================================
# 6. UI INTERFACE & TABS
# ==========================================
tab1, tab2 = st.tabs(["🔴 LIVE SCANNER", "📊 BACKTEST"])

with tab1:
    if st.button("🚀 START SCANNING (NSE 200)"):
        with st.spinner("Scanning 200 Stocks..."):
            with ThreadPoolExecutor(max_workers=20) as executor:
                res = [r for r in list(executor.map(scan_stock, stocks)) if r]
            
            if res:
                df_res = pd.DataFrame(res)
                st.dataframe(df_res, use_container_width=True)
                
                # Excel Download
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_res.to_excel(writer, index=False, sheet_name='Live_Signals')
                
                st.download_button(
                    label="📥 Download Live Signals (Excel)",
                    data=output.getvalue(),
                    file_name=f"Signals_{now.strftime('%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else: st.info("No high-probability signals found.")

with tab2:
    if st.button("📊 RUN 5-DAY BACKTEST"):
        all_bt = []
        with st.spinner("Processing Historical Data..."):
            for s in stocks:
                try:
                    df = add_indicators(all_data[s + ".NS"].dropna())
                    for i in range(30, len(df)-10):
                        row = df.iloc[i]
                        sig = None
                        if row['RVOL'] > 1.5 and row['RSI'] > 55 and row['Close'] > row['VWAP']: sig = "BUY"
                        elif row['RVOL'] > 1.5 and row['RSI'] < 45 and row['Close'] < row['VWAP']: sig = "SELL"
                        
                        if sig:
                            entry_p = row['Close']
                            sl = entry_p - (row['ATR']*1.5) if sig=="BUY" else entry_p + (row['ATR']*1.5)
                            tp = entry_p + (row['ATR']*2.5) if sig=="BUY" else entry_p - (row['ATR']*2.5)
                            
                            res_bt, exit_t = "OPEN", None
                            for j in range(i+1, min(i+60, len(df))):
                                next_r = df.iloc[j]
                                check_time = next_r.name.astimezone(IST)
                                if (sig=="BUY" and next_r['Low'] <= sl) or (sig=="SELL" and next_r['High'] >= sl):
                                    res_bt, exit_t = "LOSS", next_r.name; break
                                if (sig=="BUY" and next_r['High'] >= tp) or (sig=="SELL" and next_r['Low'] <= tp):
                                    res_bt, exit_t = "PROFIT", next_r.name; break
                                if check_time.hour == 15 and check_time.minute >= 15:
                                    res_bt = "PROFIT" if (sig=="BUY" and next_r['Close'] > entry_p) or (sig=="SELL" and next_r['Close'] < entry_p) else "LOSS"
                                    exit_t = next_r.name; break
                            
                            if res_bt != "OPEN":
                                all_bt.append({
                                    "Stock": s, "Date": row.name.strftime('%Y-%m-%d'),
                                    "Signal": sig, "RVOL": round(row['RVOL'], 2), "Entry": round(entry_p, 2),
                                    "Result": res_bt, "Duration": int((exit_t - row.name).total_seconds() / 60)
                                })
                except: continue
        
        if all_bt:
            df_bt = pd.DataFrame(all_bt)
            st.dataframe(df_bt, use_container_width=True)
            
            # Excel Download
            bt_out = io.BytesIO()
            with pd.ExcelWriter(bt_out, engine='xlsxwriter') as writer:
                df_bt.to_excel(writer, index=False, sheet_name='Backtest')
            
            st.download_button(
                label="📥 Download Backtest Report (Excel)",
                data=bt_out.getvalue(),
                file_name="Backtest_Report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else: st.warning("No trades found in backtest.")
