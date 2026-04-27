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
st.set_page_config(page_title="🔥 NSE AI PRO V11.5 - FIXED", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone('Asia/Kolkata')
current_time = datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')

st.title("🚀 NSE AI PRO V11.5 - ULTIMATE TRACKER")
st.write(f"🕒 **Last Sync (IST):** {current_time}")

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
# CORE FUNCTIONS (FIXED)
# =============================
def get_data(stock, period="2d", interval="15m"):
    try:
        df = yf.Ticker(stock + ".NS").history(period=period, interval=interval)
        return df.dropna() if not df.empty else None
    except: return None

def add_indicators(df, is_daily=False):
    df = df.copy()
    if df.empty: return df
    
    # Date Column for Grouping (Fix for ValueError)
    df['Date_Only'] = df.index.date
    
    # EMA & RSI
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-9))))
    
    # VWAP Calculation - Logic split to prevent errors
    if is_daily:
        df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
    else:
        df['VWAP'] = df.groupby('Date_Only', group_keys=False).apply(
            lambda x: (x['Close'] * x['Volume']).cumsum() / x['Volume'].cumsum()
        )
    
    # Volume Analysis (3.5x Multiplier)
    df['Vol_Avg'] = df['Volume'].rolling(20).mean()
    df['Big_Player'] = df['Volume'] > (df['Vol_Avg'] * 3.5)
    
    # Reversal Signals
    df['Bull_Rev'] = (df['RSI'].shift(1) < 30) & (df['RSI'] > 30)
    df['Bear_Rev'] = (df['RSI'].shift(1) > 70) & (df['RSI'] < 70)
    
    return df

def analyze_stock(s):
    df = get_data(s)
    if df is not None and len(df) > 15:
        df = add_indicators(df, is_daily=False)
        last = df.iloc[-1]
        score = 0
        if last['EMA20'] > last['EMA50']: score += 25
        if last['Close'] > last['VWAP']: score += 25
        if 40 < last['RSI'] < 70: score += 25
        if last['Big_Player']: score += 25
        
        sig = "WAIT"
        if score >= 75: sig = "🚀 STRONG BUY"
        elif score <= 25: sig = "💀 STRONG SELL"
        
        alert = "Normal"
        if last['Big_Player']: alert = "🐋 BIG FISH (3.5x)"
        elif last['Bull_Rev']: alert = "🔄 BULLISH REV"
        
        return {
            "STOCK": s, "PRICE": round(last['Close'], 2), 
            "SIGNAL": sig, "SMART ALERT": alert, "SCORE": score
        }
    return None

# =============================
# UI LAYOUT
# =============================
tab1, tab2, tab3 = st.tabs(["🔍 LIVE SCANNER", "📊 30-DAY BACKTEST", "📈 1-DAY CHART (SIGNALS)"])

with tab1:
    col_a, col_b = st.columns([1, 4])
    with col_a:
        sel_sec = st.selectbox("Sector", ["ALL"] + list(sector_map.keys()))
    
    if st.button("🚀 START AI SCAN"):
        targets = all_stocks if sel_sec == "ALL" else sector_map[sel_sec]
        with st.spinner("Analyzing..."):
            with ThreadPoolExecutor(max_workers=10) as executor:
                results = [r for r in list(executor.map(analyze_stock, targets)) if r is not None]
            
            if results:
                res_df = pd.DataFrame(results)
                def style_sig(val):
                    if 'BUY' in str(val): return 'background-color: #004d00; color: white'
                    if 'SELL' in str(val): return 'background-color: #4d0000; color: white'
                    return ''
                st.dataframe(res_df.style.map(style_sig, subset=['SIGNAL']), use_container_width=True)

with tab2:
    st.info("గత 30 రోజుల్లో 3.5x వాల్యూమ్ ఎంట్రీలు ఇక్కడ చూడవచ్చు.")
    if st.button("📈 RUN BACKTEST"):
        # Simplified Backtest for reliability
        bt_results = []
        for s in all_stocks[:10]:
            df_bt = yf.Ticker(s + ".NS").history(period="1mo", interval="1d")
            if not df_bt.empty:
                df_bt = add_indicators(df_bt, is_daily=True)
                signals = df_bt[df_bt['Big_Player']]
                for idx, row in signals.tail(5).iterrows():
                    bt_results.append({"DATE": idx.date(), "STOCK": s, "PRICE": round(row['Close'], 2), "TYPE": "BIG PLAYER"})
        st.table(pd.DataFrame(bt_results))

with tab3:
    selected = st.selectbox("Select Stock for Daily Analysis:", all_stocks)
    d_df = yf.Ticker(selected + ".NS").history(period="1y", interval="1d")
    
    if not d_df.empty:
        d_df = add_indicators(d_df, is_daily=True)
        
        fig = go.Figure()
        # Candlestick
        fig.add_trace(go.Candlestick(x=d_df.index, open=d_df['Open'], high=d_df['High'], low=d_df['Low'], close=d_df['Close'], name="Daily"))
        
        # EMA
        fig.add_trace(go.Scatter(x=d_df.index, y=d_df['EMA20'], line=dict(color='cyan', width=1), name="EMA 20"))
        
        # Markers
        big_p = d_df[d_df['Big_Player']]
        fig.add_trace(go.Scatter(x=big_p.index, y=big_p['Low']*0.98, mode='markers', marker=dict(symbol='diamond', size=10, color='yellow'), name="Big Player"))
        
        bull_r = d_df[d_df['Bull_Rev']]
        fig.add_trace(go.Scatter(x=bull_r.index, y=bull_r['Low']*0.97, mode='markers', marker=dict(symbol='triangle-up', size=12, color='#00ff00'), name="Buy/Rev"))
        
        fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False, title=f"{selected} Trend Analysis")
        st.plotly_chart(fig, use_container_width=True)
