import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO FINAL", layout="wide")
st_autorefresh(interval=60000, key="refresh")

st.title("🚀 MANOHAR NSE AI PRO - SMART SCANNER")
st.markdown(f"**Live Market Data | 15m Chart | Time:** {datetime.now().strftime('%H:%M:%S')}")
st.markdown("---")

# =============================
# DATA LOADER & ANALYTICS
# =============================
@st.cache_data(ttl=60)
def load_and_analyze(symbol):
    try:
        df = yf.download(symbol + ".NS", period="1d", interval="15m", progress=False)
        if df.empty or len(df) < 14:
            return None
        
        # 1. VWAP Calculation
        v_price = df['Close'] * df['Volume']
        df['VWAP'] = v_price.cumsum() / df['Volume'].cumsum()
        
        # 2. 9 EMA
        df['EMA_9'] = df['Close'].ewm(span=9, adjust=False).mean()
        
        # 3. RSI (14 Period)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # 4. Volume Spike Logic (ప్రస్తుత వాల్యూమ్ మునుపటి 5 క్యాండిల్స్ సగటు కంటే 2 రెట్లు ఎక్కువ ఉంటే)
        df['Avg_Vol'] = df['Volume'].rolling(window=5).mean()
        df['Vol_Spike'] = df['Volume'] > (df['Avg_Vol'] * 2)
        
        return df.iloc[-1], df['High'].max()
    except:
        return None

# =============================
# SECTORS
# =============================
sectors = {
    "NIFTY 50": ["RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","ITC","LT","AXISBANK","BHARTIARTL"],
    "BANKING": ["SBIN","HDFCBANK","ICICIBANK","AXISBANK","KOTAKBANK","PNB","BANKBARODA","CANBK"],
    "AUTO": ["TATAMOTORS","MARUTI","M&M","HEROMOTOCO","ASHOKLEY","TVSMOTOR"],
    "METAL": ["TATASTEEL","JSWSTEEL","HINDALCO","JINDALSTEL","SAIL","VEDL"]
}

# =============================
# DASHBOARD DISPLAY
# =============================
selected_sector = st.sidebar.selectbox("Select Sector", list(sectors.keys()))
cols = st.columns(4)

for i, stock in enumerate(sectors[selected_sector]):
    result = load_and_analyze(stock)
    
    if result:
        data, day_high = result
        last_price = data['Close']
        rsi_val = data['RSI']
        vwap_val = data['VWAP']
        vol_spike = data['Vol_Spike']
        
        with cols[i % 4]:
            with st.container(border=True):
                # ధర ట్రెండ్ బట్టి రంగు మారుతుంది
                color = "green" if last_price > vwap_val else "red"
                st.markdown(f"### :{color}[{stock}]")
                st.metric("LTP", f"₹{last_price:.2f}")
                
                # RSI Indicator
                st.write(f"📊 **RSI:** {rsi_val:.1f}")
                if rsi_val > 70: st.warning("Overbought")
                elif rsi_val < 30: st.info("Oversold")
                
                # Alerts
                if vol_spike:
                    st.error("🔊 VOLUME SPIKE!")
                
                if last_price >= day_high:
                    st.success("🎯 DAY HIGH BREAKOUT")
                
                if last_price > vwap_val and rsi_val > 55:
                    st.write("✅ **Signal: Strong Buy**")
