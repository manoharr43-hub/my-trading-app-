import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 MANOHAR NSE AI PRO V2", layout="wide")
st_autorefresh(interval=60000, key="refresh")

# Custom CSS for better look
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e2130; padding: 10px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 MANOHAR NSE AI PRO - ADVANCED TERMINAL")
st.markdown("---")

# =============================
# DIRECTION FUNCTION
# =============================
def get_direction(signal):
    if "BUY" in signal or "UP" in signal:
        return "🟢 UP"
    elif "SELL" in signal or "DOWN" in signal:
        return "🔴 DOWN"
    else:
        return "⚪ WAIT"

# =============================
# ANALYSIS FUNCTION (UPDATED WITH RSI & SMC LOGIC)
# =============================
def analyze_data(df):
    if df is None or len(df) < 25:
        return None

    # EMA Calculations
    e20 = df['Close'].ewm(span=20).mean()
    e50 = df['Close'].ewm(span=50).mean()

    # RSI Calculation (New)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # Volume & SMC Logic
    vol = df['Volume']
    avg_vol = vol.rolling(window=20).mean()
    
    curr_price = df['Close'].iloc[-1]
    curr_e20 = e20.iloc[-1]
    curr_e50 = e50.iloc[-1]
    curr_vol = vol.iloc[-1]
    curr_avg_vol = avg_vol.iloc[-1]
    curr_rsi = df['RSI'].iloc[-1]

    if pd.isna(curr_avg_vol) or curr_avg_vol == 0:
        return None

    # Trend Strength
    cp_strength = "🔵 CALL STRONG" if curr_e20 > curr_e50 else "🔴 PUT STRONG"

    # Institutional Activity (SMC)
    if curr_vol > curr_avg_vol * 2.5:
        big_player = "🐋 INSTITUTIONAL ENTRY"
    elif curr_vol > curr_avg_vol * 1.5:
        big_player = "🔥 BIG PLAYER ACTIVE"
    else:
        big_player = "💤 RETAIL VOLUME"

    observation = "WAIT"
    entry, sl, target = 0, 0, 0

    recent_high = df['High'].iloc[-10:].max()
    recent_low = df['Low'].iloc[-10:].min()
    risk = (recent_high - recent_low) if (recent_high - recent_low) > 0 else curr_price * 0.01

    # Signal Logic with RSI Filter
    if curr_e20 > curr_e50 and curr_vol > curr_avg_vol:
        if curr_rsi < 75: # Overbought filter
            observation = "🚀 CONFIRMED BUY"
            entry = curr_price
            sl = curr_price - (risk * 0.5)
            target = curr_price + risk
        else:
            observation = "⚠️ OVERBOUGHT - WAIT"

    elif curr_e20 < curr_e50 and curr_vol > curr_avg_vol:
        if curr_rsi > 25: # Oversold filter
            observation = "💀 CONFIRMED SELL"
            entry = curr_price
            sl = curr_price + (risk * 0.5)
            target = curr_price - risk
        else:
            observation = "⚠️ OVERSOLD - WAIT"

    # Trend Score Calculation
    try:
        ema_score = abs(curr_e20 - curr_e50) / curr_price * 100
        vol_score = curr_vol / curr_avg_vol
        momentum = (curr_price - df['Close'].iloc[-5]) / curr_price * 100
        
        trend_score = (ema_score * 30) + (vol_score * 10) + (abs(momentum) * 20)
        trend_score = min(100, round(trend_score, 2))
    except:
        trend_score = 0

    return (cp_strength, observation, big_player, round(entry, 2), round(sl, 2), round(target, 2), trend_score, round(curr_rsi, 2))

# =============================
# SECTORS
# =============================
all_sectors = {
    "Nifty 50": ["RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","ITC","LT","AXISBANK","BHARTIARTL"],
    "Banking": ["SBIN","AXISBANK","KOTAKBANK","HDFCBANK","ICICIBANK","PNB","CANBK","FEDERALBNK"],
    "Auto": ["TATAMOTORS","MARUTI","M&M","HEROMOTOCO","EICHERMOT","ASHOKLEY","TVSMOTOR"],
    "IT Sector": ["TCS","INFY","WIPRO","HCLTECH","TECHM","LTIM","COFORGE"]
}

# =============================
# MAIN INTERFACE
# =============================
col1, col2 = st.columns([2, 1])
with col1:
    selected_sector = st.selectbox("📂 Select Sector to Scan", list(all_sectors.keys()))
with col2:
    st.write(f"**Last Sync:** {datetime.now().strftime('%H:%M:%S')}")

stocks = all_sectors[selected_sector]

if st.button("🔍 START AI SCANNER", use_container_width=True):
    results = []
    breakout_list = []

    with st.spinner("Analyzing Market Cycles..."):
        for s in stocks:
            try:
                # Intraday 15m data
                df = yf.Ticker(s + ".NS").history(period="5d", interval="15m")
                if df.empty: continue

                res = analyze_data(df)
                if res:
                    results.append({
                        "Stock": s,
                        "Price": round(df['Close'].iloc[-1], 2),
                        "Signal": res[1],
                        "RSI": res[7],
                        "Volume Profile": res[2],
                        "Entry": res[3],
                        "SL": res[4],
                        "Target": res[5],
                        "Trend %": res[6],
                        "Direction": get_direction(res[1])
                    })

                # Opening Breakout Logic (9:15-9:30)
                today_df = df.between_time("09:15", "15:30")
                if not today_df.empty:
                    open_range = today_df.iloc[:2] # First two 15m candles
                    or_high = open_range['High'].max()
                    or_low = open_range['Low'].min()
                    
                    curr_close = today_df['Close'].iloc[-1]
                    if curr_close > or_high:
                        breakout_list.append({"Stock": s, "Type": "🚀 BULLISH BREAKOUT", "Level": round(or_high, 2)})
                    elif curr_close < or_low:
                        breakout_list.append({"Stock": s, "Type": "💀 BEARISH BREAKDOWN", "Level": round(or_low, 2)})
            except:
                continue

    # UI DISPLAY
    if results:
        df_res = pd.DataFrame(results)
        
        # Display Metrics
        m_col1, m_col2, m_col3 = st.columns(3)
        bulls = len(df_res[df_res['Direction'] == "🟢 UP"])
        bears = len(df_res[df_res['Direction'] == "🔴 DOWN"])
        
        m_col1.metric("Bullish Stocks", bulls, delta=f"{bulls} Active")
        m_col2.metric("Bearish Stocks", bears, delta=f"-{bears} Active", delta_color="inverse")
        m_col3.metric("Total Scanned", len(stocks))

        st.subheader("📊 Live Trading Signals")
        st.dataframe(df_res.style.applymap(lambda x: 'color: #00ff00' if x == "🟢 UP" else ('color: #ff4b4b' if x == "🔴 DOWN" else ''), subset=['Direction']), use_container_width=True)
    
    if breakout_list:
        st.markdown("---")
        st.subheader("⚡ High-Probability Breakouts (ORB)")
        st.table(pd.DataFrame(breakout_list))

# =============================
# BACKTEST (SIDEBAR)
# =============================
st.sidebar.header("🧪 Backtest Panel")
bt_date = st.sidebar.date_input("Analysis Date", datetime.now() - timedelta(days=1))
if st.sidebar.button("Run Historical Backtest"):
    st.sidebar.info("Backtest results will appear in the main console...")
    # (Existing backtest logic remains compatible)
