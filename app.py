import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta
import pytz
from concurrent.futures import ThreadPoolExecutor

# =============================
# CONFIG & REFRESH
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V12 - FULLY FIXED", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone('Asia/Kolkata')
current_time = datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')

st.title("🚀 NSE AI PRO V12 - THE FINAL FIX")
st.write(f"🕒 **System Time (IST):** {current_time}")

# =============================
# STOCK LIST
# =============================
stocks = ["HDFCBANK", "ICICIBANK", "SBIN", "AXISBANK", "RELIANCE", "TCS", "INFY", "TATAMOTORS", "M&M", "BAJFINANCE", "LT", "ITC"]

# =============================
# CORE FUNCTIONS (STABLE)
# =============================
def get_data(stock, period="60d", interval="1d"):
    try:
        data = yf.Ticker(stock + ".NS").history(period=period, interval=interval)
        if data.empty: return None
        # Timezone reset to avoid mapping errors
        data.index = data.index.tz_localize(None)
        return data.dropna()
    except: return None

def add_indicators(df, is_daily=True):
    df = df.copy()
    
    # Technical Indicators
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-9))))
    
    # VWAP (Simplified for Daily to avoid ValueError)
    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
    
    # Big Player (3.5x Volume)
    df['Vol_Avg'] = df['Volume'].rolling(20).mean()
    df['Big_Player'] = df['Volume'] > (df['Vol_Avg'] * 3.5)
    
    # Reversal Logic
    df['Bull_Rev'] = (df['RSI'].shift(1) < 30) & (df['RSI'] > 30)
    df['Bear_Rev'] = (df['RSI'].shift(1) > 70) & (df['RSI'] < 70)
    
    return df

# =============================
# UI - TABS
# =============================
tab1, tab2, tab3 = st.tabs(["🔍 LIVE SCANNER", "📊 30-DAY BACKTEST", "📈 TREND CHART"])

with tab1:
    if st.button("🚀 SCAN MARKET NOW"):
        results = []
        with st.spinner("Analyzing Signals..."):
            for s in stocks:
                df = get_data(s, period="5d", interval="15m") # Intraday for Scanner
                if df is not None:
                    df = add_indicators(df, is_daily=False)
                    last = df.iloc[-1]
                    
                    sig = "WAIT"
                    if last['Close'] > last['VWAP'] and last['EMA20'] > last['EMA50']: sig = "🚀 STRONG BUY"
                    elif last['Close'] < last['VWAP'] and last['EMA20'] < last['EMA50']: sig = "💀 STRONG SELL"
                    
                    alert = "Normal"
                    if last['Big_Player']: alert = "🐋 BIG FISH (3.5x)"
                    elif last['Bull_Rev']: alert = "🔄 BULLISH REV"
                    
                    # Time format fix
                    last_time = df.index[-1].strftime('%H:%M')
                    
                    results.append({
                        "STOCK": s, "TIME": last_time, "PRICE": round(last['Close'], 2),
                        "SIGNAL": sig, "ALERT": alert, "VWAP": round(last['VWAP'], 2)
                    })
        
        if results:
            res_df = pd.DataFrame(results)
            def color_sig(val):
                if 'BUY' in str(val): return 'color: #00ff00; font-weight: bold'
                if 'SELL' in str(val): return 'color: #ff4b4b; font-weight: bold'
                return ''
            st.dataframe(res_df.style.map(color_sig, subset=['SIGNAL']), use_container_width=True)

with tab2:
    st.info("గత 30 రోజుల్లో వచ్చిన పక్కా 'Big Player' ఎంట్రీలు ఇక్కడ చూడవచ్చు.")
    if st.button("📈 RUN HISTORICAL BACKTEST"):
        bt_logs = []
        with st.spinner("Fetching Back Data..."):
            for s in stocks:
                df_bt = get_data(s, period="2mo", interval="1d") # Daily for Backtest
                if df_bt is not None:
                    df_bt = add_indicators(df_bt)
                    # Filter only Big Player Entries
                    hits = df_bt[df_bt['Big_Player']]
                    for idx, row in hits.tail(5).iterrows():
                        bt_logs.append({
                            "DATE": idx.strftime('%Y-%m-%d'),
                            "STOCK": s,
                            "ENTRY PRICE": round(row['Close'], 2),
                            "SIGNAL": "🐋 BIG PLAYER ENTRY"
                        })
        if bt_logs:
            st.table(pd.DataFrame(bt_logs))
        else:
            st.warning("No Big Player entries found in the last 30 days.")

with tab3:
    selected = st.selectbox("Select stock for Chart Analysis:", stocks)
    c_df = get_data(selected, period="1y", interval="1d")
    
    if c_df is not None:
        c_df = add_indicators(c_df)
        fig = go.Figure()
        
        # Candlestick
        fig.add_trace(go.Candlestick(x=c_df.index, open=c_df['Open'], high=c_df['High'], low=c_df['Low'], close=c_df['Close'], name="Price"))
        
        # EMA & VWAP
        fig.add_trace(go.Scatter(x=c_df.index, y=c_df['EMA20'], line=dict(color='cyan', width=1), name="EMA 20"))
        fig.add_trace(go.Scatter(x=c_df.index, y=c_df['VWAP'], line=dict(color='orange', width=1.5), name="VWAP"))

        # Markers
        big_p = c_df[c_df['Big_Player']]
        fig.add_trace(go.Scatter(x=big_p.index, y=big_p['Low']*0.98, mode='markers', marker=dict(symbol='diamond', size=10, color='yellow'), name="Big Player"))
        
        bull_r = c_df[c_df['Bull_Rev']]
        fig.add_trace(go.Scatter(x=bull_r.index, y=bull_r['Low']*0.97, mode='markers', marker=dict(symbol='triangle-up', size=12, color='#00ff00'), name="Buy/Rev"))

        fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False, title=f"{selected} Trend & Entry Points")
        st.plotly_chart(fig, use_container_width=True)
