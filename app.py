import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from concurrent.futures import ThreadPoolExecutor
import io

# ==========================================
# 1. CONFIG & TIMEZONE SETUP
# ==========================================
st.set_page_config(page_title="🚀 NSE AI QUANT PRO V6.5", layout="wide")
IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI QUANT PRO - V6.5 (Backtest & Nifty Filter)")
st.subheader(f"📅 {now.strftime('%d-%b-%Y')} | 🕒 {now.strftime('%H:%M:%S')} IST")

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
def fetch_multi_day_data():
    tickers = [s + ".NS" for s in stocks] + ["^NSEI"]
    return yf.download(tickers, period="6d", interval="5m", group_by="ticker", progress=False, threads=True)

# 4. SHARED SCANNER LOGIC
def analyze_signal(df, nifty_df, i, s):
    row = df.iloc[i]
    prev = df.iloc[i-1]
    ema_dist = (row['Close'] - row['EMA20']) / row['EMA20'] * 100
    is_healthy = row['Candle_Range'] < (row['ATR'] * 1.9) and abs(ema_dist) < 0.9
    
    n_row = nifty_df.reindex(df.index, method='ffill').iloc[i]
    n_ema = nifty_df['Close'].ewm(span=20, adjust=False).mean().reindex(df.index, method='ffill').iloc[i]
    
    # BUY: Nifty > Nifty EMA20
    if n_row['Close'] > n_ema and row['Close'] > row['VWAP'] and row['RSI'] > 55:
        if is_healthy and row['Upper_Wick'] < (row['Candle_Range'] * 0.22):
            if prev['Range_Width'] < 0.45 and row['Close'] > prev['High'] and row['RVOL'] > 1.1:
                return {"TIME": row.name.strftime('%Y-%m-%d %H:%M'), "STOCK": s, "SIGNAL": "BUY", "PRICE": round(row['Close'], 2), "REASON": "🐣 Early Buy", "RVOL": round(row['RVOL'], 2), "EMA_DIST": round(ema_dist, 2), "index": i}
            elif row['RVOL'] > 2.0 and row['Close'] > prev['High20']:
                return {"TIME": row.name.strftime('%Y-%m-%d %H:%M'), "STOCK": s, "SIGNAL": "BUY", "PRICE": round(row['Close'], 2), "REASON": "🚀 Momentum Buy", "RVOL": round(row['RVOL'], 2), "EMA_DIST": round(ema_dist, 2), "index": i}

    # SELL: Nifty < Nifty EMA20
    elif n_row['Close'] < n_ema and row['Close'] < row['VWAP'] and row['RSI'] < 45:
        if is_healthy and row['Lower_Wick'] < (row['Candle_Range'] * 0.22):
            if prev['Range_Width'] < 0.45 and row['Close'] < prev['Low'] and row['RVOL'] > 1.1:
                return {"TIME": row.name.strftime('%Y-%m-%d %H:%M'), "STOCK": s, "SIGNAL": "SELL", "PRICE": round(row['Close'], 2), "REASON": "📉 Early Sell", "RVOL": round(row['RVOL'], 2), "EMA_DIST": round(ema_dist, 2), "index": i}
            elif row['RVOL'] > 2.0 and row['Close'] < prev['Low20']:
                return {"TIME": row.name.strftime('%Y-%m-%d %H:%M'), "STOCK": s, "SIGNAL": "SELL", "PRICE": round(row['Close'], 2), "REASON": "🔴 Momentum Sell", "RVOL": round(row['RVOL'], 2), "EMA_DIST": round(ema_dist, 2), "index": i}
    return None

# 5. UI TABS
tab1, tab2 = st.tabs(["🔍 TODAY'S TRACKER", "📊 5-DAY BACKTEST"])

with tab1:
    if st.button("🔍 SCAN TODAY'S MOVES"):
        all_data = fetch_multi_day_data()
        nifty_full = add_indicators(all_data["^NSEI"].dropna())
        today = now.date()
        
        today_signals = []
        for s in stocks:
            try:
                df = add_indicators(all_data[s + ".NS"].dropna())
                df_today = df[df.index.date == today]
                for idx in range(len(df_today)):
                    real_idx = df.index.get_loc(df_today.index[idx])
                    res = analyze_signal(df, nifty_full, real_idx, s)
                    if res: today_signals.append(res)
            except: continue
        
        if today_signals:
            df_show = pd.DataFrame(today_signals).sort_values(by="TIME", ascending=False)
            st.dataframe(df_show.drop(columns=['index']), use_container_width=True)
        else: st.info("నో సిగ్నల్స్ ఫౌండ్.")

with tab2:
    if st.button("📊 RUN 5-DAY HISTORICAL BACKTEST"):
        all_data = fetch_multi_day_data()
        nifty_full = add_indicators(all_data["^NSEI"].dropna())
        bt_results = []
        
        for s in stocks:
            try:
                df = add_indicators(all_data[s + ".NS"].dropna())
                for i in range(25, len(df)-12):
                    sig = analyze_signal(df, nifty_full, i, s)
                    if sig:
                        entry_p = sig['PRICE']
                        atr = df.iloc[i]['ATR']
                        sl = entry_p - (atr*1.5) if sig['SIGNAL'] == "BUY" else entry_p + (atr*1.5)
                        tp = entry_p + (atr*2.5) if sig['SIGNAL'] == "BUY" else entry_p - (atr*2.5)
                        
                        outcome, exit_time = "OPEN", None
                        for j in range(i+1, min(i+50, len(df))):
                            nxt = df.iloc[j]
                            if (sig['SIGNAL']=="BUY" and nxt['Low']<=sl) or (sig['SIGNAL']=="SELL" and nxt['High']>=sl):
                                outcome, exit_time = "LOSS", nxt.name; break
                            if (sig['SIGNAL']=="BUY" and nxt['High']>=tp) or (sig['SIGNAL']=="SELL" and nxt['Low']<=tp):
                                outcome, exit_time = "PROFIT", nxt.name; break
                        
                        if outcome != "OPEN":
                            bt_results.append({
                                "Date": sig['TIME'].split()[0], "Stock": s, "Signal": sig['SIGNAL'],
                                "Result": outcome, "Duration": int((exit_time - df.index[i]).total_seconds()/60)
                            })
            except: continue
            
        if bt_results:
            df_bt = pd.DataFrame(bt_results)
            st.success(f"బ్యాక్‌టెస్ట్ పూర్తయింది. విన్ రేట్: {round((len(df_bt[df_bt['Result']=='PROFIT'])/len(df_bt))*100, 2)}%")
            st.dataframe(df_bt, use_container_width=True)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_bt.to_excel(writer, index=False, sheet_name='Backtest')
            st.download_button("📥 Download Backtest Report", output.getvalue(), "Backtest_V6_5.xlsx")
