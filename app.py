import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta, time
import pytz

# ==========================================
# CONFIG
# ==========================================
st.set_page_config(page_title="🚀 NSE AI PRO V58 - 200 STOCKS", layout="wide")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V58 - SCREEN TIME FIXED")
st.write(f"🕒 Current Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")

# ==========================================
# NSE 200 STOCKS LIST (Sample list expanded)
# ==========================================
# నోట్: ఇక్కడ 200 స్టాక్స్ లిస్ట్ యాడ్ చేసుకోవచ్చు. ఉదాహరణకు కొన్ని ముఖ్యమైనవి ఇచ్చాను.
nse_200 = [
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "ITC", "LT", "AXISBANK", "KOTAKBANK",
    "BHARTIARTL", "HINDUNILVR", "BAJFINANCE", "ASIANPAINT", "MARUTI", "TITAN", "HCLTECH", "ADANIENT", "SUNPHARMA", "TATASTEEL",
    "WIPRO", "ULTRACEMCO", "NTPC", "JSWSTEEL", "POWERGRID", "M&M", "ONGC", "HINDALCO", "TATAMOTORS", "ADANIPORTS",
    "COALINDIA", "GRASIM", "BAJAJFINSV", "BRITANNIA", "EICHERMOT", "DIVISLAB", "CIPLA", "TECHM", "NESTLEIND", "BPCL",
    "INDUSINDBK", "HDFCLIFE", "APOLLOHOSP", "DRREDDY", "BAJAJ-AUTO", "SBILIFE", "HEROMOTOCO", "UPL", "TATACONSUM", "SHREECEM",
    # ... మీరు ఇక్కడ మిగిలిన స్టాక్స్ పేర్లను ఇదే ఫార్మాట్ లో యాడ్ చేసుకోవచ్చు
]

# ==========================================
# INDICATORS
# ==========================================
def add_indicators(df):
    if df.empty: return df
    df = df.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['Support'] = df['Low'].rolling(20).min()
    df['Resistance'] = df['High'].rolling(20).max()
    df['VolAvg'] = df['Volume'].rolling(20).mean()
    return df

def in_session(dt):
    t = dt.time()
    return time(9, 15) <= t <= time(15, 30)

def big_player(row):
    return row['Volume'] > row['VolAvg'] * 2

def get_signal(row, prev):
    if row['Close'] <= row['Support'] * 1.005: return "BUY SUPPORT"
    if row['Close'] >= row['Resistance'] * 0.995: return "SELL RESISTANCE"
    if prev['Close'] < row['EMA20'] and row['Close'] > row['EMA20']: return "BUY"
    if prev['Close'] > row['EMA20'] and row['Close'] < row['EMA20']: return "SELL"
    return None

# ==========================================
# DATA LOADING
# ==========================================
@st.cache_data(ttl=300) # 5 నిమిషాల వరకు డేటా సేవ్ అవుతుంది
def get_data(stock_list):
    tickers = [s + ".NS" for s in stock_list]
    return yf.download(tickers, period="2d", interval="5m", group_by="ticker", threads=True)

# ==========================================
# LIVE SCAN ENGINE
# ==========================================
if st.button("🚀 SCAN NSE 200 MARKET"):
    with st.spinner("200 స్టాక్స్ విశ్లేషిస్తున్నాను... దయచేసి వేచి ఉండండి..."):
        all_data = get_data(nse_200)
        results = []

        for s in nse_200:
            try:
                ticker_name = s + ".NS"
                if ticker_name not in all_data.columns.get_level_values(0): continue
                
                df = all_data[ticker_name].dropna()
                if len(df) < 20: continue
                
                df = add_indicators(df)
                row = df.iloc[-1]
                prev = df.iloc[-2]
                
                # టైమ్ కన్వర్షన్
                last_time = df.index[-1].tz_convert(IST)
                signal = get_signal(row, prev)

                if signal:
                    results.append({
                        "STOCK": s,
                        "SIGNAL TIME": last_time.strftime('%H:%M'), # కొత్త కాలమ్
                        "SIGNAL": signal,
                        "LTP": round(row['Close'], 2),
                        "SESSION": "🟢 LIVE" if in_session(last_time) else "🔴 OUTSIDE",
                        "BIG PLAYER": "🔥 YES" if big_player(row) else "NO"
                    })
            except Exception as e:
                continue

        if results:
            df_res = pd.DataFrame(results)
            st.success(f"మొత్తం {len(results)} సిగ్నల్స్ దొరికాయి!")
            st.dataframe(df_res, use_container_width=True)
        else:
            st.warning("ప్రస్తుతానికి ఎటువంటి సిగ్నల్స్ లేవు.")
