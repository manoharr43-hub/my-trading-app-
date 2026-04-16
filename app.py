import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG & UI SETUP
# =============================
st.set_page_config(page_title="🔥 MANOHAR NSE AI PRO V2", layout="wide")
st_autorefresh(interval=60000, key="refresh")

# Custom Styling
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 28px; color: #00ffcc; }
    .stDataFrame { border: 1px solid #333; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 MANOHAR NSE AI PRO - SMART TERMINAL")
st.write(f"**Live Market Feed** | Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.markdown("---")

# =============================
# DIRECTION LOGIC
# =============================
def get_direction(signal):
    if "BUY" in signal:
        return "🟢 UP"
    elif "SELL" in signal:
        return "🔴 DOWN"
    else:
        return "⚪ WAIT"

# =============================
# CORE AI ANALYSIS FUNCTION
# =============================
def analyze_data(df):
    if df is None or len(df) < 30:
        return None

    # Indicators
    e20 = df['Close'].ewm(span=20).mean()
    e50 = df['Close'].ewm(span=50).mean()
    
    # RSI Calculation
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    # Volume Analysis
    vol = df['Volume']
    avg_vol = vol.rolling(window=20).mean()
    
    curr_price = df['Close'].iloc[-1]
    curr_e20 = e20.iloc[-1]
    curr_e50 = e50.iloc[-1]
    curr_vol = vol.iloc[-1]
    curr_avg_vol = avg_vol.iloc[-1]
    curr_rsi = rsi.iloc[-1]

    # Smart Money Activity
    if curr_vol > curr_avg_vol * 2.5:
        big_player = "🐋 INSTITUTIONAL"
    elif curr_vol > curr_avg_vol * 1.5:
        big_player = "🔥 BIG PLAYER"
    else:
        big_player = "💤 RETAIL"

    observation = "WAIT"
    entry, sl, target = 0, 0, 0

    # Risk Management (ATR based simplified)
    recent_high = df['High'].iloc[-10:].max()
    recent_low = df['Low'].iloc[-10:].min()
    volatility_range = (recent_high - recent_low) if (recent_high - recent_low) > 0 else curr_price * 0.01

    # Strategy: EMA Cross + RSI Filter
    if curr_e20 > curr_e50 and curr_vol > curr_avg_vol:
        if curr_rsi < 70: # Avoid overbought
            observation = "🚀 CONFIRMED BUY"
            entry = curr_price
            sl = curr_price - (volatility_range * 0.5)
            target = curr_price + volatility_range
        else:
            observation = "⚠️ RSI OVERBOUGHT"

    elif curr_e20 < curr_e50 and curr_vol > curr_avg_vol:
        if curr_rsi > 30: # Avoid oversold
            observation = "💀 CONFIRMED SELL"
            entry = curr_price
            sl = curr_price + (volatility_range * 0.5)
            target = curr_price - volatility_range
        else:
            observation = "⚠️ RSI OVERSOLD"

    # Strength Score (0-100)
    score = min(100, round((abs(curr_e20 - curr_e50)/curr_price * 5000) + (curr_vol/curr_avg_vol * 10), 2))

    return (observation, big_player, round(entry, 2), round(sl, 2), round(target, 2), score, round(curr_rsi, 2))

# =============================
# DATA SOURCE
# =============================
sectors = {
    "Nifty 50": ["RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","ITC","LT","AXISBANK","BHARTIARTL"],
    "Banking": ["SBIN","AXISBANK","KOTAKBANK","HDFCBANK","ICICIBANK","PNB","CANBK","FEDERALBNK"],
    "Auto": ["TATAMOTORS","MARUTI","M&M","HEROMOTOCO","EICHERMOT","ASHOKLEY","TVSMOTOR"],
    "IT": ["TCS","INFY","WIPRO","HCLTECH","TECHM","LTIM"]
}

# =============================
# SIDEBAR & BACKTEST
# =============================
st.sidebar.title("🛠️ Control Panel")
selected_sector = st.sidebar.selectbox("Select Sector", list(sectors.keys()))
bt_date = st.sidebar.date_input("Backtest Date", datetime.now() - timedelta(days=1))

# =============================
# MAIN SCANNER EXECUTION
# =============================
if st.button("🔍 START LIVE AI SCAN", use_container_width=True):
    results = []
    
    with st.spinner(f"Scanning {selected_sector} Stocks..."):
        for s in sectors[selected_sector]:
            try:
                data = yf.Ticker(s + ".NS").history(period="5d", interval="15m")
                if data.empty: continue
                
                analysis = analyze_data(data)
                if analysis:
                    results.append({
                        "Stock": s,
                        "Price": round(data['Close'].iloc[-1], 2),
                        "Signal": analysis[0],
                        "RSI": analysis[6],
                        "Player": analysis[1],
                        "Entry": analysis[2],
                        "StopLoss": analysis[3],
                        "Target": analysis[4],
                        "Score": analysis[5],
                        "Direction": get_direction(analysis[0])
                    })
            except Exception as e:
                continue

    if results:
        df_final = pd.DataFrame(results)
        
        # Summary Metrics
        c1, c2, c3 = st.columns(3)
        up_count = len(df_final[df_final['Direction'] == "🟢 UP"])
        down_count = len(df_final[df_final['Direction'] == "🔴 DOWN"])
        
        c1.metric("Bullish 📈", up_count)
        c2.metric("Bearish 📉", down_count)
        c3.metric("Scanned", len(results))

        st.subheader("📊 Trade Signals Table")
        
        # FIXED: Using .map() instead of .applymap() to avoid AttributeError
        styled_df = df_final.style.map(
            lambda x: 'color: #00ff00; font-weight: bold' if x == "🟢 UP" else ('color: #ff4b4b; font-weight: bold' if x == "🔴 DOWN" else ''),
            subset=['Direction']
        )
        
        st.dataframe(styled_df, use_container_width=True)
    else:
        st.error("No signals found at this moment.")

# =============================
# FOOTER
# =============================
st.markdown("---")
st.caption("Developed for Manohar | NSE AI Pro Terminal | 2026")
