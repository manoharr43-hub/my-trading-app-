import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# =============================
# 1. CONFIGURATION
# =============================
st.set_page_config(page_title="MANOHAR NSE AI PRO", layout="wide")
st_autorefresh(interval=60000, key="refresh") # ప్రతి నిమిషానికి అప్‌డేట్ అవుతుంది

st.title("🚀 MANOHAR NSE AI PRO - SMART SCANNER")
st.write(f"అప్‌డేట్ సమయం: {datetime.now().strftime('%H:%M:%S')}")
st.markdown("---")

# =============================
# 2. ANALYSIS FUNCTION
# =============================
@st.cache_data(ttl=60)
def analyze_stock(symbol):
    try:
        # 1-Day డేటా, 15 నిమిషాల ఇంటర్వల్
        df = yf.download(symbol + ".NS", period="1d", interval="15m", progress=False)
        
        if df.empty or len(df) < 14:
            return None

        # VWAP Calculation
        v_price = df['Close'] * df['Volume']
        df['VWAP'] = v_price.cumsum() / df['Volume'].cumsum()

        # RSI (14) Calculation
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # Volume Spike (గత 5 క్యాండిల్స్ సగటు కంటే 2 రెట్లు ఎక్కువ)
        avg_vol = df['Volume'].iloc[-6:-1].mean()
        curr_vol = df['Volume'].iloc[-1]
        vol_spike = curr_vol > (avg_vol * 2)

        return {
            "LTP": df['Close'].iloc[-1],
            "VWAP": df['VWAP'].iloc[-1],
            "RSI": df['RSI'].iloc[-1],
            "High": df['High'].max(),
            "Vol_Spike": vol_spike
        }
    except:
        return None

# =============================
# 3. SECTORS
# =============================
sectors = {
    "NIFTY 50": ["RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","ITC","LT","AXISBANK","BHARTIARTL"],
    "BANKING": ["SBIN","HDFCBANK","ICICIBANK","AXISBANK","KOTAKBANK","PNB","BANKBARODA","CANBK"],
    "AUTO": ["TATAMOTORS","MARUTI","M&M","HEROMOTOCO","ASHOKLEY","TVSMOTOR"],
    "METAL": ["TATASTEEL","JSWSTEEL","HINDALCO","JINDALSTEL","SAIL","VEDL"]
}

# =============================
# 4. DISPLAY DASHBOARD
# =============================
selected_sector = st.sidebar.selectbox("Sector ఎంచుకోండి", list(sectors.keys()))
stocks = sectors[selected_sector]

cols = st.columns(4) # 4 కాలమ్స్ గా చూపిస్తుంది

for i, stock in enumerate(stocks):
    res = analyze_stock(stock)
    
    if res:
        with cols[i % 4]:
            # బాక్స్ డిజైన్
            with st.container(border=True):
                # ధర VWAP పైన ఉంటే గ్రీన్, కింద ఉంటే రెడ్
                header_color = "green" if res['LTP'] > res['VWAP'] else "red"
                st.markdown(f"### :{header_color}[{stock}]")
                
                st.metric("ధర (LTP)", f"₹{res['LTP']:.2f}")
                st.write(f"📊 **RSI:** {res['RSI']:.1f}")
                
                # ముఖ్యమైన అలర్ట్స్
                if res['Vol_Spike']:
                    st.error("🔊 VOLUME SPIKE
