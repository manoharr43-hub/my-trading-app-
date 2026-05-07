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
st.set_page_config(page_title="🚀 NSE AI QUANT PRO V6.6", layout="wide")
IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI QUANT PRO - V6.6")
st.subheader(f"🕒 Current Time: {now.strftime('%H:%M:%S')} IST")

# 2. NSE 200 STOCKS LIST
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

# 3. INDICATORS ENGINE
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
    tr = pd.concat([df['High']-df['Low'], (df['High']-df['Close'].shift()).abs(), (df['Low']-df['Close'].shift()).abs()], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()
    df['VolAvg'] = df['Volume'].rolling(20).mean()
    df['RVOL'] = df['Volume'] / (df['VolAvg'] + 1e-9)
    df['High20'] = df['High'].rolling(window=20).max()
    df['Low20'] = df['Low'].rolling(window=20).min()
    df['Range_Width'] = (df['High20'] - df['Low20']) / df['Low20'] * 100
    df['Candle_Range'] = df['High'] - df['Low']
    df['Upper_Wick'] = df['High'] - df[['Open', 'Close']].max(axis=1)
    df['Lower_Wick'] = df[['Open', 'Close']].min(axis=1) - df['Low']
    return df

@st.cache_data(ttl=60)
def fetch_data(period="1d"):
    tickers = [s + ".NS" for s in stocks] + ["^NSEI"]
    return yf.download(tickers, period=period, interval="5m", group_by="ticker", progress=False, threads=True)

# 4. CORE SCAN LOGIC
def scan_logic(df, nifty_df, i, s):
    row = df.iloc[i]
    prev = df.iloc[i-1]
    ema_dist = (row['Close'] - row['EMA20']) / row['EMA20'] * 100
    is_healthy = row['Candle_Range'] < (row['ATR'] * 1.9) and abs(ema_dist) < 0.9
    
    n_row = nifty_df.reindex(df.index, method='ffill').iloc[i]
    n_ema = nifty_df['Close'].ewm(span=20, adjust=False).mean().reindex(df.index, method='ffill').iloc[i]
    
    # BUY CONDITION
    if n_row['Close'] > n_ema and row['Close'] > row['VWAP'] and row['RSI'] > 55:
        if is_healthy and row['Upper_Wick'] < (row['Candle_Range'] * 0.22):
            if (prev['Range_Width'] < 0.45 and row['Close'] > prev['High']) or row['RVOL'] > 2.0:
                return {"TIME": row.name.astimezone(IST).strftime('%H:%M'), "STOCK": s, "SIGNAL": "BUY", "PRICE": round(row['Close'], 2), "RVOL": round(row['RVOL'], 2), "EMA_DIST": f"{round(ema_dist, 2)}%"}

    # SELL CONDITION
    elif n_row['Close'] < n_ema and row['Close'] < row['VWAP'] and row['RSI'] < 45:
        if is_healthy and row['Lower_Wick'] < (row['Candle_Range'] * 0.22):
            if (prev['Range_Width'] < 0.45 and row['Close'] < prev['Low']) or row['RVOL'] > 2.0:
                return {"TIME": row.name.astimezone(IST).strftime('%H:%M'), "STOCK": s, "SIGNAL": "SELL", "PRICE": round(row['Close'], 2), "RVOL": round(row['RVOL'], 2), "EMA_DIST": f"{round(ema_dist, 2)}%"}
    return None

# 5. UI INTERFACE
tab1, tab2 = st.tabs(["🔍 LIVE TRACKER", "📊 5-DAY BACKTEST"])

with tab1:
    if st.button("🔍 START SCAN"):
        all_data = fetch_data("1d")
        nifty = add_indicators(all_data["^NSEI"].dropna())
        res_list = []
        for s in stocks:
            try:
                df = add_indicators(all_data[s + ".NS"].dropna())
                for idx in range(25, len(df)):
                    res = scan_logic(df, nifty, idx, s)
                    if res: res_list.append(res)
            except: continue
        
        if res_list:
            df_res = pd.DataFrame(res_list).sort_values(by="TIME", ascending=False)
            st.dataframe(df_res, use_container_width=True)
            
            # Excel Download
            out = io.BytesIO()
            with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
                df_res.to_excel(writer, index=False, sheet_name='Today_Signals')
            st.download_button("📥 Download Excel Report", out.getvalue(), "Today_Signals.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else: st.info("No signals right now.")

with tab2:
    if st.button("📊 RUN BACKTEST"):
        bt_data = fetch_data("6d")
        nifty = add_indicators(bt_data["^NSEI"].dropna())
        bt_res = []
        for s in stocks:
            try:
                df = add_indicators(bt_data[s + ".NS"].dropna())
                for i in range(25, len(df)-12):
                    sig = scan_logic(df, nifty, i, s)
                    if sig:
                        # Simple SL/TGT logic
                        entry = sig['PRICE']
                        atr = df.iloc[i]['ATR']
                        sl = entry - (atr*1.5) if sig['SIGNAL']=="BUY" else entry + (atr*1.5)
                        tp = entry + (atr*2.5) if sig['SIGNAL']=="BUY" else entry - (atr*2.5)
                        
                        for j in range(i+1, min(i+50, len(df))):
                            nxt = df.iloc[j]
                            if (sig['SIGNAL']=="BUY" and nxt['Low']<=sl) or (sig['SIGNAL']=="SELL" and nxt['High']>=sl):
                                bt_res.append({"Stock": s, "Signal": sig['SIGNAL'], "Result": "LOSS"}); break
                            if (sig['SIGNAL']=="BUY" and nxt['High']>=tp) or (sig['SIGNAL']=="SELL" and nxt['Low']<=tp):
                                bt_res.append({"Stock": s, "Signal": sig['SIGNAL'], "Result": "PROFIT"}); break
            except: continue
        
        if bt_res:
            df_bt = pd.DataFrame(bt_res)
            st.success(f"Backtest Complete! Total Trades: {len(df_bt)}")
            st.dataframe(df_bt, use_container_width=True)
            # Excel Download
            bt_out = io.BytesIO()
            with pd.ExcelWriter(bt_out, engine='xlsxwriter') as writer:
                df_bt.to_excel(writer, index=False, sheet_name='Backtest')
            st.download_button("📥 Download Backtest Excel", bt_out.getvalue(), "Backtest_Report.xlsx")
