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

st.title("🚀 MANOHAR NSE AI PRO - TERMINAL")
st.markdown("---")

# =============================
# SIDEBAR - BREAKOUT SETTINGS
# =============================
st.sidebar.header("⚙️ Breakout Structure Settings")
# బ్రేక్-అవుట్ సమయాన్ని ఇక్కడ నిమిషాల్లో సెట్ చేయండి
duration_mins = st.sidebar.slider("Select Breakout Range (Minutes)", 15, 60, 30, step=15)
start_time_str = "09:15"
# ఎండ్ టైమ్ లెక్కించడం
start_dt = datetime.strptime(start_time_str, "%H:%M")
end_dt = start_dt + timedelta(minutes=duration_mins)
end_time_str = end_dt.strftime("%H:%M")

st.sidebar.info(f"Scanning for Breakouts after {end_time_str}")

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

    # EMA & RSI Logic
    e20 = df['Close'].ewm(span=20).mean()
    e50 = df['Close'].ewm(span=50).mean()
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    vol = df['Volume']
    avg_vol = vol.rolling(window=20).mean()
    
    curr_price = df['Close'].iloc[-1]
    curr_rsi = rsi.iloc[-1]
    curr_vol = vol.iloc[-1]
    curr_avg_vol = avg_vol.iloc[-1]

    big_player = "🐋 INSTITUTIONAL" if curr_vol > curr_avg_vol * 2.0 else "💤 RETAIL"
    
    observation = "WAIT"
    entry, sl, target = 0, 0, 0
    recent_high, recent_low = df['High'].iloc[-10:].max(), df['Low'].iloc[-10:].min()
    risk = (recent_high - recent_low) if (recent_high - recent_low) > 0 else curr_price * 0.01

    if e20.iloc[-1] > e50.iloc[-1] and curr_vol > curr_avg_vol and curr_rsi < 70:
        observation = "🚀 CONFIRMED BUY"
        entry, sl, target = curr_price, curr_price - (risk*0.5), curr_price + risk
    elif e20.iloc[-1] < e50.iloc[-1] and curr_vol > curr_avg_vol and curr_rsi > 30:
        observation = "💀 CONFIRMED SELL"
        entry, sl, target = curr_price, curr_price + (risk*0.5), curr_price - risk

    return (observation, big_player, round(entry, 2), round(sl, 2), round(target, 2), round(curr_rsi, 2))

# =============================
# SECTORS
# =============================
all_sectors = {
    "Nifty 50": ["RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","ITC","LT","AXISBANK","BHARTIARTL"],
    "Banking": ["SBIN","AXISBANK","KOTAKBANK","HDFCBANK","ICICIBANK","PNB","CANBK","FEDERALBNK"],
    "Auto": ["TATAMOTORS","MARUTI","M&M","HEROMOTOCO","EICHERMOT","ASHOKLEY","TVSMOTOR"]
}

selected_sector = st.selectbox("📂 Select Sector", list(all_sectors.keys()))
stocks = all_sectors[selected_sector]

# =============================
# SCANNER EXECUTION
# =============================
if st.button("🔍 START LIVE SCANNER", use_container_width=True):
    results = []
    breakout_results = []

    # ఇక్కడ ఎర్రర్ ఫిక్స్ చేశాను (Corrected f-string)
    with st.spinner(f"Scanning for {duration_mins}M Range Breakouts..."):
        for s in stocks:
            try:
                df = yf.Ticker(s + ".NS").history(period="5d", interval="15m")
                if df.empty: continue

                # 1. Normal Signal
                res = analyze_data(df)
                if res:
                    results.append({
                        "Stock": s, "Price": round(df['Close'].iloc[-1], 2),
                        "Signal": res[0], "RSI": res[5], "Player": res[1],
                        "Entry": res[2], "SL": res[3], "Target": res[4],
                        "Direction": get_direction(res[0])
                    })

                # 2. Breakout with Time mention
                today = df.between_time("09:15", "15:30")
                num_candles = duration_mins // 15
                
                if len(today) > num_candles:
                    range_df = today.iloc[0:num_candles]
                    orb_high = range_df['High'].max()
                    orb_low = range_df['Low'].min()
                    curr_price = today['Close'].iloc[-1]

                    if curr_price > orb_high:
                        breakout_results.append({
                            "Stock": s,
                            "Range Period": f"{start_time_str} - {end_time_str}",
                            "Breakout Level": round(orb_high, 2),
                            "Current Price": round(curr_price, 2),
                            "Signal": "🚀 BULLISH BREAK",
                            "Direction": "🟢 UP"
                        })
                    elif curr_price < orb_low:
                        breakout_results.append({
                            "Stock": s,
                            "Range Period": f"{start_time_str} - {end_time_str}",
                            "Breakout Level": round(orb_low, 2),
                            "Current Price": round(curr_price, 2),
                            "Signal": "💀 BEARISH BREAK",
                            "Direction": "🔴 DOWN"
                        })
            except: continue

    # TABLES DISPLAY
    if results:
        st.subheader("📊 Live Trading Signals")
        # Fixed .map() for coloring
        st.dataframe(pd.DataFrame(results).style.map(lambda x: 'color: #00ff00' if x == "🟢 UP" else ('color: #ff4b4b' if x == "🔴 DOWN" else ''), subset=['Direction']), use_container_width=True)

    if breakout_results:
        st.markdown("---")
        st.subheader(f"⚡ {duration_mins} Min Range Breakout Details")
        st.dataframe(pd.DataFrame(breakout_results).style.map(lambda x: 'color: #00ff00' if x == "🟢 UP" else ('color: #ff4b4b' if x == "🔴 DOWN" else ''), subset=['Direction']), use_container_width=True)
