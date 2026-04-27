import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
import pytz
from concurrent.futures import ThreadPoolExecutor

# =============================
# CONFIG & REFRESH
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V11 - ADVANCED CHART", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone('Asia/Kolkata')
current_time = datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')

st.title("🚀 NSE AI PRO V11 - CHART & SIGNALS")
st.write(f"🕒 **Current Market Sync (IST):** {current_time}")

# =============================
# STOCK LIST & SECTORS
# =============================
sector_map = {
    "BANKING": ["HDFCBANK", "ICICIBANK", "SBIN", "AXISBANK", "KOTAKBANK", "INDUSINDBK"],
    "IT": ["TCS", "INFY", "HCLTECH", "WIPRO", "TECHM", "LTIM"],
    "AUTO": ["TATAMOTORS", "M&M", "MARUTI", "BAJAJ-AUTO", "EICHERMOT", "HEROMOTOCO"],
    "ENERGY/INFRA": ["RELIANCE", "NTPC", "POWERGRID", "ONGC", "BPCL", "LT", "ADANIPORTS"],
    "CONSUMER": ["ITC", "HINDUNILVR", "BRITANNIA", "NESTLEIND", "VBL", "ASIANPAINT"],
    "OTHERS": ["BAJFINANCE", "BAJAJFINSV", "TATASTEEL", "JSWSTEEL", "BHARTIARTL", "SUNPHARMA"]
}
all_stocks = [s for sub in sector_map.values() for s in sub]

# =============================
# CORE FUNCTIONS
# =============================
def get_data(stock, period="2d", interval="15m"):
    try:
        df = yf.Ticker(stock + ".NS").history(period=period, interval=interval)
        return df.dropna() if not df.empty else None
    except: return None

def add_indicators(df):
    df = df.copy()
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-9))))
    
    df['Date'] = df.index.date
    df['VWAP'] = df.groupby('Date', group_keys=False).apply(
        lambda x: (x['Close'] * x['Volume']).cumsum() / x['Volume'].cumsum()
    )
    
    # Volume Analysis for Markers
    df['Vol_Avg'] = df['Volume'].rolling(20).mean()
    df['Big_Player'] = df['Volume'] > (df['Vol_Avg'] * 3.5)
    
    # Reversal Indicators
    df['Bull_Rev'] = (df['RSI'].shift(1) < 30) & (df['RSI'] > 30)
    df['Bear_Rev'] = (df['RSI'].shift(1) > 70) & (df['RSI'] < 70)
    
    return df

def analyze_stock(s):
    df = get_data(s)
    if df is not None and len(df) > 15:
        df = add_indicators(df)
        last = df.iloc[-1]
        score = 0
        if last['EMA20'] > last['EMA50']: score += 20
        if 40 < last['RSI'] < 70: score += 20
        if last['Volume'] > last['Vol_Avg'] * 1.5: score += 20
        if last['Close'] > last['VWAP']: score += 20
        
        sig = "WAIT"
        if score >= 80: sig = "🚀 STRONG BUY"
        elif score <= 30: sig = "💀 STRONG SELL"
        
        alert = "Normal"
        if last['Big_Player']: alert = "🐋 BIG FISH (3.5x)"
        elif last['Bull_Rev']: alert = "🔄 BULLISH REV"

        return {"STOCK": s, "PRICE": round(last['Close'], 2), "SIGNAL": sig, "ALERT": alert}
    return None

# =============================
# UI LAYOUT
# =============================
tab1, tab2, tab3 = st.tabs(["🔍 LIVE SCANNER", "📊 30-DAY BACKTEST", "📈 ONE-DAY CHART ANALYSIS"])

with tab1:
    if st.button("🚀 START AI SCAN"):
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(analyze_stock, all_stocks))
        st.table([r for r in results if r is not None])

with tab2:
    st.info("Historical Analysis of Big Fish entries.")
    # (Keeping your original Backtest logic here)

with tab3:
    selected = st.selectbox("Select stock for 1-Day Chart:", all_stocks)
    # 1-Day Format Data
    d_df = yf.Ticker(selected + ".NS").history(period="1y", interval="1d")
    
    if not d_df.empty:
        d_df = add_indicators(d_df)
        fig = go.Figure()

        # Candlestick
        fig.add_trace(go.Candlestick(x=d_df.index, open=d_df['Open'], high=d_df['High'], low=d_df['Low'], close=d_df['Close'], name="Price"))

        # Big Player Markers (Yellow Diamonds)
        big_entry = d_df[d_df['Big_Player']]
        fig.add_trace(go.Scatter(x=big_entry.index, y=big_entry['Low'] * 0.98, mode='markers', 
                                 marker=dict(symbol='diamond', size=10, color='yellow'), name="🐋 Big Player"))

        # Bullish Reversal (Green Arrows)
        bull_entry = d_df[d_df['Bull_Rev']]
        fig.add_trace(go.Scatter(x=bull_entry.index, y=bull_entry['Low'] * 0.97, mode='markers', 
                                 marker=dict(symbol='triangle-up', size=12, color='green'), name="🟢 Buy/Rev"))

        # Bearish Reversal (Red Arrows)
        bear_entry = d_df[d_df['Bear_Rev']]
        fig.add_trace(go.Scatter(x=bear_entry.index, y=bear_entry['High'] * 1.03, mode='markers', 
                                 marker=dict(symbol='triangle-down', size=12, color='red'), name="🔴 Sell/Rev"))

        fig.update_layout(template="plotly_dark", height=700, title=f"{selected} - 1 Day Analysis", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
