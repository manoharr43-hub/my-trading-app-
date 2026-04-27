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
st.set_page_config(page_title="🚀 NSE AI PRO V32", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V32 - PULLBACK MASTER (FIXED)")
st.write(f"🕒 **Market Time:** {now.strftime('%Y-%m-%d %H:%M:%S')}")

# =============================
# STOCK LIST
# =============================
stocks = [
    "RELIANCE","TCS","HDFCBANK","ICICIBANK","INFY","BHARTIARTL",
    "SBIN","ITC","LT","BAJFINANCE","AXISBANK","KOTAKBANK",
    "HCLTECH","MARUTI","SUNPHARMA","TITAN","TATAMOTORS",
    "ULTRACEMCO","ADANIENT","JSWSTEEL","M&M","NTPC","POWERGRID"
]

# =============================
# CORE INDICATORS
# =============================
def add_indicators(df, interval='5m'):
    df = df.copy()
    if len(df) < 20: return df
    
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-9)
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))
    
    high_low = df['High'] - df['Low']
    tr = pd.concat([high_low, abs(df['High'] - df['Close'].shift()), abs(df['Low'] - df['Close'].shift())], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()
    df['VolAvg'] = df['Volume'].rolling(20).mean()
    
    if interval == '1d':
        df['PP'] = (df['High'] + df['Low'] + df['Close']) / 3
        df['S1'] = (2 * df['PP']) - df['High']
        df['R1'] = (2 * df['PP']) - df['Low']
    return df

@st.cache_data(ttl=60)
def fetch_data(symbols, interval, period):
    tickers = [s + ".NS" for s in symbols]
    return yf.download(tickers, period=period, interval=interval, group_by='ticker', progress=False)

data_5m = fetch_data(stocks, "5m", "5d")
data_1d = fetch_data(stocks, "1d", "6mo")

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()

# =============================
# TABS
# =============================
tab1, tab2 = st.tabs(["🔥 LIVE PULLBACK SCANNER", "📊 FULL DAY BACKTEST"])

# -----------------------------
# TAB 1: LIVE SCANNER
# -----------------------------
with tab1:
    if st.button("RUN SCANNER"):
        results = []
        for s in stocks:
            try:
                df1 = add_indicators(data_1d[s + ".NS"].dropna(), '1d')
                df5 = add_indicators(data_5m[s + ".NS"].dropna(), '5m')
                l1, l5 = df1.iloc[-2], df5.iloc[-1]
                
                curr_p, ema, s1, r1 = l5['Close'], l5['EMA20'], l1['S1'], l1['R1']
                atr = l5['ATR']
                
                # BUY Pullback Logic
                if (abs(curr_p - s1)/s1 < 0.003 or abs(curr_p - ema)/ema < 0.003) and curr_p > l5['Open']:
                    results.append({
                        "TIME": df5.index[-1].astimezone(IST).strftime('%H:%M'),
                        "STOCK": s, "ACTION": "BUY 🟢 (Support)", "ENTRY": round(curr_p, 2),
                        "SL": round(curr_p - atr, 2), "TARGET": round(curr_p + (atr*2), 2),
                        "BIG PLAYER": "🔥" if l5['Volume'] > l5['VolAvg']*2 else "-"
                    })
                # SELL Pullback Logic
                elif (abs(curr_p - r1)/r1 < 0.003 or abs(curr_p - ema)/ema < 0.003) and curr_p < l5['Open']:
                    results.append({
                        "TIME": df5.index[-1].astimezone(IST).strftime('%H:%M'),
                        "STOCK": s, "ACTION": "SELL 🔴 (Resistance)", "ENTRY": round(curr_p, 2),
                        "SL": round(curr_p + atr, 2), "TARGET": round(curr_p - (atr*2), 2),
                        "BIG PLAYER": "🔥" if l5['Volume'] > l5['VolAvg']*2 else "-"
                    })
            except: continue
        
        if results:
            st.table(pd.DataFrame(results))
        else:
            st.info("No Pullback signals found at this moment.")

# -----------------------------
# TAB 2: BACKTEST (FIXED SYNTAX)
# -----------------------------
with tab2:
    bt_date = st.date_input("Backtest Date", value=now.date() - timedelta(days=1))
    if st.button("RUN BACKTEST"):
        bt_logs = []
        for s in stocks:
            try:
                df = data_5m[s + ".NS"].dropna()
                df.index = df.index.tz_convert(IST)
                df_day = add_indicators(df[df.index.date == bt_date])
                
                if df_day is None or df_day.empty: continue

                for i in range(15, len(df_day)):
                    row = df_day.iloc[i]
                    dist = abs(row['Close'] - row['EMA20']) / row['EMA20']
                    
                    if dist < 0.004:
                        action = "BUY 🟢" if row['Close'] > row['Open'] else "SELL 🔴"
                        bt_logs.append({
                            "TIME": df_day.index[i].strftime('%H:%M'),
                            "STOCK": s, "TYPE": action, "PRICE": round(row['Close'], 2)
                        })
            except Exception as e:
                continue # ఇక్కడ except బ్లాక్ పెట్టడం వల్ల మీ పాత ఎర్రర్ రాదు
        
        if bt_logs:
            st.dataframe(pd.DataFrame(bt_logs), use_container_width=True)
        else:
            st.warning("No data found for this date.")
