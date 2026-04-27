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
st.set_page_config(page_title="🔥 NSE AI PRO V11 - CHART SPECIAL", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone('Asia/Kolkata')
current_time = datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')

st.title("🚀 NSE AI PRO V11 - ONE DAY ANALYSIS")
st.write(f"🕒 **System Sync (IST):** {current_time}")

# =============================
# STOCK LIST
# =============================
stocks = ["HDFCBANK", "ICICIBANK", "SBIN", "RELIANCE", "TCS", "INFY", "TATAMOTORS", "M&M", "BAJFINANCE", "LT", "BHARTIARTL", "ITC"]

# =============================
# CORE FUNCTIONS
# =============================
def get_data(stock, period="60d", interval="1d"): # 1 Day Format Setup
    try:
        df = yf.Ticker(stock + ".NS").history(period=period, interval=interval)
        return df.dropna() if not df.empty else None
    except: return None

def add_indicators(df):
    df = df.copy()
    # Indicators
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-9))))
    
    # Volume Analysis for Big Player (3.5x)
    df['Vol_Avg'] = df['Volume'].rolling(20).mean()
    df['Big_Player'] = df['Volume'] > (df['Vol_Avg'] * 3.5)
    
    # Reversal Logic
    df['Prev_RSI'] = df['RSI'].shift(1)
    df['Bull_Rev'] = (df['Prev_RSI'] < 30) & (df['RSI'] > 30)
    df['Bear_Rev'] = (df['Prev_RSI'] > 70) & (df['RSI'] < 70)
    
    return df

# =============================
# UI LAYOUT
# =============================
tab1, tab2 = st.tabs(["📈 ONE DAY CHART ANALYSIS", "🔍 QUICK SCANNER"])

with tab1:
    selected = st.selectbox("Select Stock for Day Chart:", stocks)
    # Fetching 1 Day interval data
    c_df = get_data(selected, period="1y", interval="1d")
    
    if c_df is not None:
        c_df = add_indicators(c_df)
        
        fig = go.Figure()

        # 1. Candlestick Chart
        fig.add_trace(go.Candlestick(
            x=c_df.index, open=c_df['Open'], high=c_df['High'], 
            low=c_df['Low'], close=c_df['Close'], name="Daily Price"
        ))

        # 2. EMA Lines
        fig.add_trace(go.Scatter(x=c_df.index, y=c_df['EMA20'], line=dict(color='cyan', width=1.5), name="EMA 20"))
        fig.add_trace(go.Scatter(x=c_df.index, y=c_df['EMA50'], line=dict(color='orange', width=1.5), name="EMA 50"))

        # 3. BIG PLAYER ENTRY MARKERS (Yellow Diamonds)
        big_entry = c_df[c_df['Big_Player']]
        fig.add_trace(go.Scatter(
            x=big_entry.index, y=big_entry['Low'] * 0.98,
            mode='markers', marker=dict(symbol='diamond', size=12, color='yellow'),
            name="🐋 BIG PLAYER ENTRY"
        ))

        # 4. BULLISH REVERSAL MARKERS (Green Arrows)
        bull_rev = c_df[c_df['Bull_Rev']]
        fig.add_trace(go.Scatter(
            x=bull_rev.index, y=bull_rev['Low'] * 0.97,
            mode='markers', marker=dict(symbol='triangle-up', size=15, color='#00ff00'),
            name="🔄 BULLISH REVERSAL"
        ))

        # 5. BEARISH REVERSAL MARKERS (Red Arrows)
        bear_rev = c_df[c_df['Bear_Rev']]
        fig.add_trace(go.Scatter(
            x=bear_rev.index, y=bear_rev['High'] * 1.03,
            mode='markers', marker=dict(symbol='triangle-down', size=15, color='#ff0000'),
            name="🔄 BEARISH REVERSAL"
        ))

        fig.update_layout(
            title=f"{selected} - Daily Chart (Signals & Big Player Entry)",
            template="plotly_dark",
            height=700,
            xaxis_rangeslider_visible=False,
            yaxis_title="Price (INR)"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Info Box
        st.markdown("""
        **Chart Legend:**
        * 🟡 **Yellow Diamond:** Big Player Entry (High Volume > 3.5x)
        * 🟢 **Green Arrow:** Bullish Reversal (RSI coming out of Oversold)
        * 🔴 **Red Arrow:** Bearish Reversal (RSI falling from Overbought)
        """)

with tab2:
    if st.button("Run Quick Day Scan"):
        results = []
        for s in stocks:
            df = get_data(s, period="30d", interval="1d")
            if df is not None:
                df = add_indicators(df)
                last = df.iloc[-1]
                status = "NORMAL"
                if last['Big_Player']: status = "🐋 BIG PLAYER ENTRY"
                elif last['Bull_Rev']: status = "🔄 BULLISH REVERSAL"
                
                results.append({"STOCK": s, "CLOSE": round(last['Close'], 2), "STATUS": status, "RSI": round(last['RSI'], 2)})
        
        st.table(pd.DataFrame(results))
