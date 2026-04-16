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

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 28px; color: #00ffcc; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 MANOHAR NSE AI PRO - TERMINAL")
st.write(f"**Last Update:** {datetime.now().strftime('%H:%M:%S')}")
st.markdown("---")

# =============================
# DIRECTION LOGIC
# =============================
def get_direction(signal):
    if "BUY" in signal or "BULLISH" in signal:
        return "🟢 UP"
    elif "SELL" in signal or "BEARISH" in signal:
        return "🔴 DOWN"
    else:
        return "⚪ WAIT"

# =============================
# CORE ANALYSIS FUNCTION
# =============================
def analyze_data(df):
    if df is None or len(df) < 25:
        return None

    # Indicators
    e20 = df['Close'].ewm(span=20).mean()
    e50 = df['Close'].ewm(span=50).mean()
    
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    vol = df['Volume']
    avg_vol = vol.rolling(window=20).mean()
    
    curr_price = df['Close'].iloc[-1]
    curr_e20 = e20.iloc[-1]
    curr_e50 = e50.iloc[-1]
    curr_vol = vol.iloc[-1]
    curr_avg_vol = avg_vol.iloc[-1]
    curr_rsi = rsi.iloc[-1]

    # Institutional Activity
    if curr_vol > curr_avg_vol * 2.0:
        big_player = "🐋 INSTITUTIONAL"
    elif curr_vol > curr_avg_vol * 1.5:
        big_player = "🔥 BIG PLAYER"
    else:
        big_player = "💤 RETAIL"

    observation = "WAIT"
    entry, sl, target = 0, 0, 0
    recent_high = df['High'].iloc[-10:].max()
    recent_low = df['Low'].iloc[-10:].min()
    risk = (recent_high - recent_low) if (recent_high - recent_low) > 0 else curr_price * 0.01

    # Signal Logic
    if curr_e20 > curr_e50 and curr_vol > curr_avg_vol:
        if curr_rsi < 70:
            observation = "🚀 CONFIRMED BUY"
            entry, sl, target = curr_price, curr_price - (risk*0.5), curr_price + risk
        else:
            observation = "⚠️ RSI OVERBOUGHT"
    elif curr_e20 < curr_e50 and curr_vol > curr_avg_vol:
        if curr_rsi > 30:
            observation = "💀 CONFIRMED SELL"
            entry, sl, target = curr_price, curr_price + (risk*0.5), curr_price - risk
        else:
            observation = "⚠️ RSI OVERSOLD"

    score = min(100, round((curr_vol/curr_avg_vol)*15 + 20, 2))
    return (observation, big_player, round(entry, 2), round(sl, 2), round(target, 2), score, round(curr_rsi, 2))

# =============================
# SECTORS
# =============================
all_sectors = {
    "Nifty 50": ["RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","ITC","LT","AXISBANK","BHARTIARTL"],
    "Banking": ["SBIN","AXISBANK","KOTAKBANK","HDFCBANK","ICICIBANK","PNB","CANBK","FEDERALBNK"],
    "Auto": ["TATAMOTORS","MARUTI","M&M","HEROMOTOCO","EICHERMOT","ASHOKLEY","TVSMOTOR"],
    "IT": ["TCS","INFY","WIPRO","HCLTECH","TECHM","LTIM"]
}

selected_sector = st.selectbox("📂 Select Sector", list(all_sectors.keys()))
stocks = all_sectors[selected_sector]

# =============================
# SCANNER EXECUTION
# =============================
if st.button("🔍 START LIVE SCANNER", use_container_width=True):
    results = []
    breakout_results = []

    with st.spinner("AI Scanning Market..."):
        for s in stocks:
            try:
                df = yf.Ticker(s + ".NS").history(period="5d", interval="15m")
                if df.empty: continue

                # 1. Normal Signal Analysis
                res = analyze_data(df)
                if res:
                    results.append({
                        "Stock": s,
                        "Price": round(df['Close'].iloc[-1], 2),
                        "Signal": res[0],
                        "RSI": res[6],
                        "Player": res[1],
                        "Entry": res[2],
                        "SL": res[3],
                        "Target": res[4],
                        "Score": res[5],
                        "Direction": get_direction(res[0])
                    })

                # 2. Breakout Analysis (Same Table Format)
                today = df.between_time("09:15", "15:30")
                if len(today) >= 2:
                    orb_high = today.iloc[0:2]['High'].max() # First 30 mins
                    orb_low = today.iloc[0:2]['Low'].min()
                    curr_price = today['Close'].iloc[-1]

                    if curr_price > orb_high:
                        breakout_results.append({
                            "Stock": s,
                            "Price": round(curr_price, 2),
                            "Signal": "🚀 BULLISH BREAKOUT",
                            "Level": round(orb_high, 2),
                            "Player": "🔥 BREAKOUT",
                            "Direction": "🟢 UP"
                        })
                    elif curr_price < orb_low:
                        breakout_results.append({
                            "Stock": s,
                            "Price": round(curr_price, 2),
                            "Signal": "💀 BEARISH BREAKDOWN",
                            "Level": round(orb_low, 2),
                            "Player": "💀 BREAKDOWN",
                            "Direction": "🔴 DOWN"
                        })
            except:
                continue

    # DISPLAY RESULTS
    if results:
        st.subheader("📊 Live Trading Signals")
        df_res = pd.DataFrame(results)
        st.dataframe(df_res.style.map(lambda x: 'color: #00ff00' if x == "🟢 UP" else ('color: #ff4b4b' if x == "🔴 DOWN" else ''), subset=['Direction']), use_container_width=True)

    if breakout_results:
        st.markdown("---")
        st.subheader("⚡ High-Probability Breakout Stocks")
        df_brk = pd.DataFrame(breakout_results)
        st.dataframe(df_brk.style.map(lambda x: 'color: #00ff00' if x == "🟢 UP" else ('color: #ff4b4b' if x == "🔴 DOWN" else ''), subset=['Direction']), use_container_width=True)
    else:
        st.info("No Breakouts detected in this sector yet.")

st.sidebar.markdown("---")
st.sidebar.caption("NSE AI Pro Terminal v2.0")
