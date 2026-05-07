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
st.set_page_config(page_title="🚀 NSE AI QUANT PRO V6.4", layout="wide")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

# UI Styling
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1f2937; padding: 15px; border-radius: 10px; border: 1px solid #374151; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 NSE AI QUANT PRO - V6.4 (Early Buy & Sell)")
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
def fetch_today_data():
    tickers = [s + ".NS" for s in stocks] + ["^NSEI"]
    return yf.download(tickers, period="1d", interval="5m", group_by="ticker", progress=False, threads=True)

all_data = fetch_today_data()

# ==========================================
# 4. BUY & SELL TRACKER LOGIC
# ==========================================
def track_all_signals(s):
    try:
        ticker = s + ".NS"
        df = add_indicators(all_data[ticker].dropna())
        nifty = all_data["^NSEI"].dropna()
        signals = []
        for i in range(25, len(df)):
            row = df.iloc[i]
            prev = df.iloc[i-1]
            ema_dist = (row['Close'] - row['EMA20']) / row['EMA20'] * 100
            is_healthy = row['Candle_Range'] < (row['ATR'] * 1.9) and abs(ema_dist) < 0.9
            n_row = nifty.reindex(df.index, method='ffill').iloc[i]
            n_trend = "UP" if n_row['Close'] > n_row['Open'] else "DOWN"

            # BUY LOGIC
            if n_trend == "UP" and row['Close'] > row['VWAP'] and row['RSI'] > 55:
                if is_healthy and row['Upper_Wick'] < (row['Candle_Range'] * 0.22):
                    if prev['Range_Width'] < 0.45 and row['Close'] > prev['High'] and row['RVOL'] > 1.1:
                        signals.append({"TIME": row.name.astimezone(IST).strftime('%H:%M'), "STOCK": s, "SIGNAL": "BUY", "PRICE": round(row['Close'], 2), "REASON": "🐣 Early Buy", "RVOL": round(row['RVOL'], 2), "EMA_DIST": f"{round(ema_dist, 2)}%"})
                    elif row['RVOL'] > 2.0 and row['Close'] > prev['High20']:
                        signals.append({"TIME": row.name.astimezone(IST).strftime('%H:%M'), "STOCK": s, "SIGNAL": "BUY", "PRICE": round(row['Close'], 2), "REASON": "🚀 Momentum Buy", "RVOL": round(row['RVOL'], 2), "EMA_DIST": f"{round(ema_dist, 2)}%"})

            # SELL LOGIC
            elif n_trend == "DOWN" and row['Close'] < row['VWAP'] and row['RSI'] < 45:
                if is_healthy and row['Lower_Wick'] < (row['Candle_Range'] * 0.22):
                    if prev['Range_Width'] < 0.45 and row['Close'] < prev['Low'] and row['RVOL'] > 1.1:
                        signals.append({"TIME": row.name.astimezone(IST).strftime('%H:%M'), "STOCK": s, "SIGNAL": "SELL", "PRICE": round(row['Close'], 2), "REASON": "📉 Early Sell", "RVOL": round(row['RVOL'], 2), "EMA_DIST": f"{round(ema_dist, 2)}%"})
                    elif row['RVOL'] > 2.0 and row['Close'] < prev['Low20']:
                        signals.append({"TIME": row.name.astimezone(IST).strftime('%H:%M'), "STOCK": s, "SIGNAL": "SELL", "PRICE": round(row['Close'], 2), "REASON": "🔴 Momentum Sell", "RVOL": round(row['RVOL'], 2), "EMA_DIST": f"{round(ema_dist, 2)}%"})
        return signals
    except: return []

# ==========================================
# 5. UI INTERFACE
# ==========================================
if st.button("🔍 SCAN TODAY'S BUY & SELL MOVES"):
    with st.spinner("మార్కెట్ అంతా వెతుకుతున్నాను..."):
        with ThreadPoolExecutor(max_workers=20) as executor:
            all_results = list(executor.map(track_all_signals, stocks))
        final_signals = [sig for sublist in all_results for sig in sublist]
        if final_signals:
            df_final = pd.DataFrame(final_signals).sort_values(by="TIME", ascending=False)
            st.dataframe(df_final, use_container_width=True)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_final.to_excel(writer, index=False, sheet_name='Signals')
            st.download_button("📥 Download Report", output.getvalue(), f"V6_4_{now.strftime('%d%m')}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else: st.info("నో సిగ్నల్స్ ఫౌండ్.")
