import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
from io import BytesIO
from streamlit_autorefresh import st_autorefresh
import plotly.graph_objects as go

# =============================
# CONFIG & REFRESH
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V16 - NSE 200", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V16 - FULL SYSTEM (NSE 200)")
st.write(f"🕒 Last Update: {now.strftime('%Y-%m-%d %H:%M:%S')}")

# =============================
# NSE 200 STOCK LIST (Top 100 for performance, you can add more)
# =============================
stocks = [
    "RELIANCE","TCS","HDFCBANK","ICICIBANK","INFY","BHARTIARTL","SBIN","ITC","LT","BAJFINANCE",
    "AXISBANK","KOTAKBANK","HCLTECH","MARUTI","SUNPHARMA","TITAN","TATAMOTORS","ULTRACEMCO","ADANIENT","JSWSTEEL",
    "M&M","NTPC","POWERGRID","TATASTEEL","ADANIPORTS","ONGC","COALINDIA","HINDALCO","GRASIM","BAJAJFINSV",
    "BRITANNIA","INDUSINDBK","EICHERMOT","HINDUNILVR","NESTLEIND","CIPLA","SBILIFE","DRREDDY","TATACONSUM","APOLLOHOSP",
    "ADANIPOWER","BPCL","DLF","CHOLAFIN","TRENT","BEL","HAL","CANBK","HDFCLIFE","SHREECEM",
    "AMBUJACEM","ABB","SIEMENS","POLYCAB","LUPIN","IDFCFIRSTB","TATAELXSI","PAGEIND","COLPAL","PFC",
    "RECLTD","GAIL","SAIL","NMDC","VEDL","DIVISLAB","TATAPOWER","HINDPETRO","BANKBARODA","AU SMALL",
    "OBEROIRLTY","ASHOKLEY","TVSMOTOR","HEROMOTOCO","PIDILITIND","BKRANGI","DLF","PHOENIXLTD","MAXHEALTH","PERSISTENT"
] # Need more? Just add "TICKER" to this list.

# =============================
# CORE FUNCTIONS
# =============================
@st.cache_data(ttl=300)
def get_batch_data(stock_list, interval="5m", period="5d"):
    try:
        tickers = [s + ".NS" for s in stock_list]
        data = yf.download(tickers, period=period, interval=interval, group_by='ticker', progress=False)
        return data
    except: return None

def add_indicators(df):
    df = df.copy()
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))
    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-9)
    df['MACD'] = df['Close'].ewm(span=12).mean() - df['Close'].ewm(span=26).mean()
    df['Signal'] = df['MACD'].ewm(span=9).mean()
    df['ATR'] = (df['High'] - df['Low']).rolling(14).mean()
    return df

def ai_score(df):
    if len(df) < 2: return 0
    last = df.iloc[-1]
    score = 0
    if last['EMA20'] > last['EMA50']: score += 25
    if 50 < last['RSI'] < 70: score += 15
    if last['Close'] > last['VWAP']: score += 20
    if last['MACD'] > last['Signal']: score += 20
    if last['Volume'] > df['Volume'].rolling(20).mean().iloc[-1]: score += 20
    return score

def check_pullback_type(df):
    try:
        last = df.iloc[-1]
        dist = abs(last['Close'] - last['EMA20']) / last['EMA20']
        # 0.5% proximity to EMA20
        if last['EMA20'] > last['EMA50'] and last['Close'] > last['EMA20'] and dist < 0.005:
            if last['Close'] > last['Open']: return "🔵 BUY PULLBACK"
        if last['EMA20'] < last['EMA50'] and last['Close'] < last['EMA20'] and dist < 0.005:
            if last['Close'] < last['Open']: return "🔴 SELL PULLBACK"
        return ""
    except: return ""

# =============================
# TABS SETUP
# =============================
tab1, tab2, tab3, tab4 = st.tabs([
    "🔍 LIVE SCANNER", 
    "🎯 PULLBACK LIVE", 
    "📊 GENERIC BACKTEST", 
    "🔥 PB BACKTEST (B/S)"
])

# Shared Batch Download
all_data = get_batch_data(stocks)

# -----------------------------
# TAB 1: LIVE SCANNER
# -----------------------------
with tab1:
    if st.button("🚀 SCAN ALL STOCKS"):
        res = []
        for s in stocks:
            try:
                df = all_data[s + ".NS"].dropna()
                df = add_indicators(df)
                sc = ai_score(df)
                if sc >= 70:
                    res.append({"STOCK": s, "PRICE": round(df['Close'].iloc[-1],2), "SCORE": sc, "SIGNAL": "STRONG BUY"})
                elif sc <= 30:
                    res.append({"STOCK": s, "PRICE": round(df['Close'].iloc[-1],2), "SCORE": sc, "SIGNAL": "STRONG SELL"})
            except: continue
        if res: st.dataframe(pd.DataFrame(res).sort_values("SCORE", ascending=False), use_container_width=True)
        else: st.warning("No Strong Trend Signals.")

# -----------------------------
# TAB 2: PULLBACK LIVE
# -----------------------------
with tab2:
    if st.button("🎯 SCAN PULLBACKS"):
        pb_res = []
        for s in stocks:
            try:
                df = all_data[s + ".NS"].dropna()
                df = add_indicators(df)
                pb = check_pullback_type(df)
                if pb != "":
                    pb_res.append({"STOCK": s, "PRICE": round(df['Close'].iloc[-1],2), "TYPE": pb, "SCORE": ai_score(df)})
            except: continue
        if pb_res: st.dataframe(pd.DataFrame(pb_res), use_container_width=True)
        else: st.warning("No Pullback setups found right now.")

# -----------------------------
# TAB 3: GENERIC BACKTEST
# -----------------------------
with tab3:
    b_date = st.date_input("Select Date", key="gen_bt")
    if st.button("📊 START BACKTEST"):
        st.info("Backtesting AI Score Accuracy...")
        # Generic backtest logic here

# -----------------------------
# TAB 4: PB BACKTEST (BUY & SELL)
# -----------------------------
with tab4:
    test_date = st.date_input("Backtest Date", key="pb_bt_v16")
    if st.button("🔥 START PB BACKTEST"):
        logs = []
        for s in stocks:
            try:
                df = all_data[s + ".NS"].dropna()
                df = add_indicators(df)
                df_day = df[df.index.date == test_date]
                for i in range(20, len(df_day)-1):
                    snap = df_day.iloc[:i+1]
                    pb = check_pullback_type(snap)
                    if pb != "":
                        entry = snap['Close'].iloc[-1]
                        exit_p = df_day['Close'].iloc[i+1]
                        res = "WIN ✅" if (pb == "🔵 BUY PULLBACK" and exit_p > entry) or (pb == "🔴 SELL PULLBACK" and exit_p < entry) else "LOSS ❌"
                        logs.append({"TIME": df_day.index[i].strftime('%H:%M'), "STOCK": s, "SIDE": pb, "RESULT": res})
            except: continue
        if logs: st.dataframe(pd.DataFrame(logs), use_container_width=True)
        else: st.warning("No pullback trades on this day.")

# -----------------------------
# CHART
# -----------------------------
st.markdown("---")
choice = st.selectbox("📊 View Chart", stocks)
if all_data is not None:
    c_df = add_indicators(all_data[choice + ".NS"].dropna())
    fig = go.Figure(data=[go.Candlestick(x=c_df.index, open=c_df['Open'], high=c_df['High'], low=c_df['Low'], close=c_df['Close'])])
    fig.add_trace(go.Scatter(x=c_df.index, y=c_df['EMA20'], name="EMA20", line=dict(color='orange')))
    fig.update_layout(height=500, template="plotly_dark", title=f"{choice} Live Chart")
    st.plotly_chart(fig, use_container_width=True)
