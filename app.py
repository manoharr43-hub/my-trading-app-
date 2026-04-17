import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 MANOHAR NSE AI PRO", layout="wide")
st_autorefresh(interval=60000, key="refresh")

# =============================
# HEADER
# =============================
st.title("🚀 MANOHAR NSE AI PRO TERMINAL")
st.markdown("---")

# =============================
# DIRECTION FUNCTION
# =============================
def get_direction(signal):
    if signal == "🚀 CONFIRMED BUY":
        return "🟢 UP"
    elif signal == "💀 CONFIRMED SELL":
        return "🔴 DOWN"
    elif signal == "⚠️ FAILED SELL → BUY":
        return "🟢 UP"
    elif signal == "⚠️ FAILED BUY → SELL":
        return "🔴 DOWN"
    else:
        return "⚪ WAIT"

# =============================
# ANALYSIS FUNCTION
# =============================
def analyze_data(df):
    if df is None or len(df) < 20:
        return None

    e20 = df['Close'].ewm(span=20).mean()
    e50 = df['Close'].ewm(span=50).mean()
    vol = df['Volume']
    avg_vol = vol.rolling(window=20).mean()

    curr_price = df['Close'].iloc[-1]
    curr_e20 = e20.iloc[-1]
    curr_e50 = e50.iloc[-1]
    curr_vol = vol.iloc[-1]
    curr_avg_vol = avg_vol.iloc[-1]

    if pd.isna(curr_avg_vol) or curr_avg_vol == 0:
        return None

    cp_strength = "🔵 CALL STRONG" if curr_e20 > curr_e50 else "🔴 PUT STRONG"

    if curr_vol > curr_avg_vol * 2:
        big_player = "🔥 EXTREME INSTITUTIONAL"
    elif curr_vol > curr_avg_vol * 1.5:
        big_player = "🐋 BIG PLAYER ACTIVE"
    else:
        big_player = "💤 NORMAL"

    observation = "WAIT"
    entry, sl, target = 0, 0, 0

    recent_high = df['High'].iloc[-10:].max()
    recent_low = df['Low'].iloc[-10:].min()
    risk = (recent_high - recent_low) if (recent_high - recent_low) > 0 else curr_price * 0.01

    if curr_e20 > curr_e50 and curr_vol > curr_avg_vol:
        observation = "🚀 CONFIRMED BUY"
        entry = curr_price
        sl = curr_price - (risk * 0.5)
        target = curr_price + risk
    elif curr_e20 < curr_e50 and curr_vol > curr_avg_vol:
        observation = "💀 CONFIRMED SELL"
        entry = curr_price
        sl = curr_price + (risk * 0.5)
        target = curr_price - risk

    try:
        ema_score = abs(curr_e20 - curr_e50) / curr_price * 100
        vol_score = curr_vol / curr_avg_vol
        momentum = (curr_price - df['Close'].iloc[-5]) / curr_price * 100
        range_strength = (recent_high - recent_low) / curr_price * 100
        trend_score = (
            ema_score * 0.3 +
            vol_score * 20 * 0.3 +
            abs(momentum) * 0.2 +
            range_strength * 0.2
        )
        trend_score = min(100, round(trend_score, 2))
    except:
        trend_score = 0

    return (
        cp_strength,
        observation,
        big_player,
        round(entry, 2),
        round
