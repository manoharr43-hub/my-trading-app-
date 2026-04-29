import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta, time
import pytz

# ==========================================
# CONFIG
# ==========================================
st.set_page_config(page_title="🚀 NSE AI PRO V58", layout="wide")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V58 - BACKTEST & 200 STOCKS")
st.write(f"🕒 ప్రస్తుత సమయం: {now.strftime('%Y-%m-%d %H:%M:%S')}")

# ==========================================
# NSE 200 STOCKS LIST (Sample)
# ==========================================
# ఇక్కడ మీరు పూర్తి 200 స్టాక్స్ లిస్ట్ పెట్టుకోవచ్చు
nse_200 = [
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "ITC", "LT", "AXISBANK", "KOTAKBANK",
    "BHARTIARTL", "HINDUNILVR", "BAJFINANCE", "ASIANPAINT", "MARUTI", "TITAN", "HCLTECH", "ADANIENT", "SUNPHARMA", "TATASTEEL",
    "WIPRO", "ULTRACEMCO", "NTPC", "JSWSTEEL", "POWERGRID", "M&M", "ONGC", "HINDALCO", "TATAMOTORS", "ADANIPORTS",
    "COALINDIA", "GRASIM", "BAJAJFINSV", "BRITANNIA", "EICHERMOT", "DIVISLAB", "CIPLA", "TECHM", "NESTLEIND", "BPCL",
    "INDUSINDBK", "HDFCLIFE", "APOLLOHOSP", "DRREDDY", "BAJAJ-AUTO", "SBILIFE", "HEROMOTOCO", "UPL", "TATACONSUM", "SHREECEM"
]

# ==========================================
# INDICATORS FUNCTION
# ==========================================
def add_indicators(df):
    if df.empty: return df
    df = df.copy()
    # MultiIndex కాలమ్స్ ఉంటే క్లీన్ చేస్తుంది
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
    if row['Close'] <= row['Support'] * 1.002: return "🔵 BUY SUPPORT"
    if row['Close'] >= row['Resistance'] * 0.998: return "🔴 SELL RESISTANCE"
    if prev['Close'] < prev['EMA20'] and row['Close'] > row['EMA20']: return "🟢 BUY CROSS"
    if prev['Close'] > prev['EMA20'] and row['Close'] < row['EMA20']: return "🟠 SELL CROSS"
    return None

# ==========================================
# DATA FETCHING
# ==========================================
@st.cache_data(ttl=300)
def get_data(stock_list, period="5d"):
    tickers = [s + ".NS" for s in stock_list]
    return yf.download(tickers, period=period, interval="5m", group_by="ticker", threads=True)

# ==========================================
# UI TABS: LIVE SCAN & BACKTEST
# ==========================================
tab1, tab2 = st.tabs(["🚀 LIVE SCANNER", "📊 HISTORICAL BACKTEST"])

with tab1:
    if st.button("🚀 START LIVE SCAN (NSE 200)"):
        data = get_data(nse_200, period="2d")
        live_results = []
        
        for s in nse_200:
            try:
                df = data[s+".NS"].dropna()
                if len(df) < 20: continue
                df = add_indicators(df)
                row, prev = df.iloc[-1], df.iloc[-2]
                st_time = df.index[-1].tz_convert(IST)
                
                sig = get_signal(row, prev)
                if sig:
                    live_results.append({
                        "STOCK": s,
                        "SIGNAL TIME": st_time.strftime('%H:%M'),
                        "SIGNAL": sig,
                        "PRICE": round(row['Close'], 2),
                        "BIG PLAYER": "🔥 YES" if big_player(row) else "NO"
                    })
            except: continue
        
        if live_results:
            st.dataframe(pd.DataFrame(live_results), use_container_width=True)
        else:
            st.info("ప్రస్తుతానికి ఎటువంటి లైవ్ సిగ్నల్స్ లేవు.")

with tab2:
    col1, col2 = st.columns(2)
    with col1:
        test_date = st.date_input("Backtest తేదీని ఎంచుకోండి", now.date() - timedelta(days=1))
    
    if st.button("📊 RUN FULL BACKTEST"):
        # Backtest కోసం ఎక్కువ డేటా డౌన్‌లోడ్ చేస్తున్నాం
        data = get_data(nse_200, period="7d")
        backtest_logs = []
        
        with st.spinner(f"{test_date} నాటి డేటాను విశ్లేషిస్తున్నాను..."):
            for s in nse_200:
                try:
                    df_all = data[s+".NS"].dropna()
                    df_all.index = df_all.index.tz_convert(IST)
                    
                    # ఎంచుకున్న తేదీ డేటాను మాత్రమే ఫిల్టర్ చేయడం
                    df = df_all[df_all.index.date == test_date].copy()
                    if len(df) < 20: continue
                    
                    df = add_indicators(df)
                    
                    for i in range(1, len(df)):
                        row = df.iloc[i]
                        prev = df.iloc[i-1]
                        
                        # కేవలం మార్కెట్ సెషన్ లో వచ్చిన సిగ్నల్స్ మాత్రమే
                        if in_session(df.index[i]):
                            sig = get_signal(row, prev)
                            if sig:
                                backtest_logs.append({
                                    "TIME": df.index[i].strftime('%H:%M'),
                                    "STOCK": s,
                                    "SIGNAL": sig,
                                    "ENTRY PRICE": round(row['Close'], 2),
                                    "BIG PLAYER": "🔥 YES" if big_player(row) else "NO"
                                })
                except: continue
        
        if backtest_logs:
            bt_df = pd.DataFrame(backtest_logs)
            st.success(f"మొత్తం {len(backtest_logs)} సిగ్నల్స్ లభించాయి.")
            # సమయం ప్రకారం క్రమ పద్ధతిలో అమర్చడం
            st.dataframe(bt_df.sort_values(by="TIME", ascending=False), use_container_width=True)
        else:
            st.warning("ఆ తేదీన ఎటువంటి సిగ్నల్స్ రికార్డ్ కాలేదు.")
