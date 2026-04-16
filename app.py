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

st.title("🚀 MANOHAR NSE AI PRO - LIVE TERMINAL")
st.markdown("---")

# =============================
# SIDEBAR - SETTINGS
# =============================
st.sidebar.header("⚙️ Breakout Detection Settings")
duration_mins = st.sidebar.selectbox("Range Setup (Mins)", [15, 30, 45, 60], index=1)
st.sidebar.info(f"Detecting breakouts based on first {duration_mins}m range across the day.")

# =============================
# DIRECTION LOGIC
# =============================
def get_direction(signal):
    if "BUY" in signal or "UP" in signal:
        return "🟢 UP"
    elif "SELL" in signal or "DOWN" in signal:
        return "🔴 DOWN"
    else:
        return "⚪ WAIT"

# =============================
# SCANNER EXECUTION
# =============================
all_sectors = {
    "Nifty 50": ["RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","ITC","LT","AXISBANK","BHARTIARTL"],
    "Banking": ["SBIN","AXISBANK","KOTAKBANK","HDFCBANK","ICICIBANK","PNB","CANBK","FEDERALBNK"],
    "Auto": ["TATAMOTORS","MARUTI","M&M","HEROMOTOCO","EICHERMOT","ASHOKLEY","TVSMOTOR"]
}

selected_sector = st.selectbox("📂 Select Sector", list(all_sectors.keys()))
stocks = all_sectors[selected_sector]

if st.button("🔍 START FULL DAY SCANNER", use_container_width=True):
    breakout_history = []

    with st.spinner("Scanning Full Day Price Action..."):
        for s in stocks:
            try:
                # 1 నిమిషం డేటా తీసుకుంటే బ్రేక్-అవుట్ టైమ్ ఖచ్చితంగా తెలుస్తుంది
                df = yf.Ticker(s + ".NS").history(period="1d", interval="5m")
                if df.empty: continue

                # మార్నింగ్ రేంజ్ లెక్కించడం (First X mins)
                num_candles = duration_mins // 5
                range_df = df.iloc[0:num_candles]
                orb_high = range_df['High'].max()
                orb_low = range_df['Low'].min()

                # రోజంతా చెక్ చేయడం
                for i in range(num_candles, len(df)):
                    curr_row = df.iloc[i]
                    prev_row = df.iloc[i-1]
                    curr_time = df.index[i].strftime('%H:%M')

                    # Bullish Breakout Check
                    if prev_row['Close'] <= orb_high and curr_row['Close'] > orb_high:
                        breakout_history.append({
                            "Stock": s,
                            "Breakout Time": curr_time,
                            "Signal": "🚀 BULLISH BREAK",
                            "Level": round(orb_high, 2),
                            "Current Price": round(curr_row['Close'], 2),
                            "Direction": "🟢 UP"
                        })
                        break # ఒక స్టాక్‌కి ఒకసారి బ్రేక్ చూపిస్తే చాలు

                    # Bearish Breakdown Check
                    elif prev_row['Close'] >= orb_low and curr_row['Close'] < orb_low:
                        breakout_history.append({
                            "Stock": s,
                            "Breakout Time": curr_time,
                            "Signal": "💀 BEARISH BREAK",
                            "Level": round(orb_low, 2),
                            "Current Price": round(curr_row['Close'], 2),
                            "Direction": "🔴 DOWN"
                        })
                        break
            except: continue

    # DISPLAY TABLE
    st.subheader(f"📅 Full Day Breakout History ({duration_mins}m Range)")
    if breakout_history:
        df_final = pd.DataFrame(breakout_history)
        
        # టైమ్ ప్రకారం సార్ట్ చేయడం (Latest breakouts first)
        df_final = df_final.sort_values(by="Breakout Time", ascending=False)
        
        st.dataframe(
            df_final.style.map(
                lambda x: 'color: #00ff00; font-weight: bold' if x == "🟢 UP" else ('color: #ff4b4b; font-weight: bold' if x == "🔴 DOWN" else ''), 
                subset=['Direction']
            ), 
            use_container_width=True
        )
    else:
        st.info("No breakouts detected yet today.")

st.markdown("---")
st.caption("Note: This scans 5-minute intervals to find the exact minute of the breakout.")
