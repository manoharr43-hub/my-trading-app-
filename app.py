import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
import os

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V21", layout="wide")
st.title("🚀 NSE AI PRO V21 (Big Player + Trend + S/R)")
st_autorefresh(interval=60000, key="refresh")

# =============================
# BACKTEST FOLDER
# =============================
BACKTEST_DIR = "backtests"
os.makedirs(BACKTEST_DIR, exist_ok=True)

# =============================
# SESSION
# =============================
if "live_big" not in st.session_state:
    st.session_state.live_big = []

# =============================
# SECTOR MAP
# =============================
sector_map = {
    "Banking": ["HDFCBANK","ICICIBANK","SBIN","AXISBANK","KOTAKBANK"],
    "IT": ["INFY","TCS","HCLTECH","WIPRO","TECHM"],
    "Pharma": ["SUNPHARMA","DRREDDY","CIPLA","DIVISLAB"],
    "Auto": ["MARUTI","M&M","TATAMOTORS","HEROMOTOCO","BAJAJ-AUTO"],
    "Metals": ["JSWSTEEL","TATASTEEL","HINDALCO","VEDL"],
    "FMCG": ["ITC","HINDUNILVR","NESTLEIND","BRITANNIA","DABUR"],
    "Oil & Gas": ["RELIANCE","ONGC","BPCL","IOC","GAIL"],
    "Infra": ["LT","ADANIPORTS","POWERGRID","NTPC"],
    "Telecom": ["BHARTIARTL","IDEA"]
}

selected_sector = st.sidebar.selectbox("📂 Select Sector", list(sector_map.keys()))
stocks = sector_map[selected_sector]

# =============================
# FUNCTIONS
# =============================
def clean_time(ts):
    return pd.to_datetime(ts).strftime("%I:%M %p").lstrip("0")

@st.cache_data(ttl=60)
def load_data(stock, interval="5m"):
    try:
        df = yf.Ticker(stock + ".NS").history(period="1d", interval=interval)
        return df.between_time("09:15","15:30") if not df.empty else pd.DataFrame()
    except:
        return pd.DataFrame()

# ===== 15m TREND =====
@st.cache_data(ttl=60)
def get_15m_trend(stock):
    df = load_data(stock, "15m")
    if df.empty or len(df) < 20:
        return "UNKNOWN"
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    return "UP" if df['Close'].iloc[-1] > df['EMA20'].iloc[-1] else "DOWN"

# ===== SUPPORT / RESISTANCE =====
def get_sr_levels(df, window=20):
    if df.empty: return []
    highs = df['High'].rolling(window).max()
    lows = df['Low'].rolling(window).min()
    return highs.iloc[-1], lows.iloc[-1]

# ===== BIG PLAYER =====
def big_player(df, stock):
    if df.empty or len(df) < 30:
        return []
    df = df.copy()
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    tp = (df['High'] + df['Low'] + df['Close']) / 3
    df['VWAP'] = (tp * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1)
    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    rs = gain.rolling(14).mean() / (loss.rolling(14).mean() + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))
    df['AvgVol'] = df['Volume'].rolling(20).mean()

    entries, last_signal = [], None
    for i in range(25, len(df)):
        price = df['Close'].iloc[i]
        vol = df['Volume'].iloc[i] > df['AvgVol'].iloc[i] * 1.5
        buy = price > df['EMA20'].iloc[i] and price > df['VWAP'].iloc[i] and df['RSI'].iloc[i] > 52
        sell = price < df['EMA20'].iloc[i] and price < df['VWAP'].iloc[i] and df['RSI'].iloc[i] < 48
        if vol and buy and last_signal != "BUY":
            entries.append({"Stock":stock,"Type":"BIG BUY","Price":price,"TimeRaw":df.index[i],"Time":clean_time(df.index[i]),"Confidence":"HIGH"})
            last_signal = "BUY"
        elif vol and sell and last_signal != "SELL":
            entries.append({"Stock":stock,"Type":"BIG SELL","Price":price,"TimeRaw":df.index[i],"Time":clean_time(df.index[i]),"Confidence":"HIGH"})
            last_signal = "SELL"
    return entries[-10:]

# =============================
# LIVE
# =============================
if st.button("🔍 START LIVE"):
    filtered_signals = []
    for s in stocks:
        df = load_data(s, "5m")
        signals = big_player(df, s)
        trend = get_15m_trend(s)
        sr_high, sr_low = get_sr_levels(df)
        for sig in signals:
            if trend == "UP" and sig["Type"] == "BIG BUY" and sig["Price"] > sr_high:
                filtered_signals.append(sig)
            elif trend == "DOWN" and sig["Type"] == "BIG SELL" and sig["Price"] < sr_low:
                filtered_signals.append(sig)
    st.session_state.live_big = sorted(filtered_signals, key=lambda x: x["TimeRaw"])

# =============================
# DISPLAY
# =============================
if st.session_state.live_big:
    df_signals = pd.DataFrame(st.session_state.live_big)
    st.subheader("🐋 HQ FILTERED SIGNALS (Big Player + Trend + S/R)")
    st.dataframe(df_signals)
    stock = st.selectbox("📈 Chart", stocks)
    df_chart = load_data(stock, "5m")
    if not df_chart.empty:
        trend = get_15m_trend(stock)
        sr_high, sr_low = get_sr_levels(df_chart)
        st.markdown(f"📊 15m Trend: **{trend}** | Resistance: {sr_high:.2f} | Support: {sr_low:.2f}")
        fig = go.Figure(data=[go.Candlestick(
            x=df_chart.index, open=df_chart['Open'], high=df_chart['High'],
            low=df_chart['Low'], close=df_chart['Close']
        )])
        df_big = df_signals[df_signals["Stock"] == stock]
        for _, row in df_big.iterrows():
            fig.add_trace(go.Scatter(
                x=[row["TimeRaw"]], y=[row["Price"]],
                mode="markers", marker=dict(size=10, color="green" if row["Type"]=="BIG BUY" else "red")
            ))
        # Draw S/R lines
        fig.add_hline(y=sr_high, line_dash="dot", line_color="blue", annotation_text="Resistance")
        fig.add_hline(y=sr_low, line_dash="dot", line_color="orange", annotation_text="Support")
        st.plotly_chart(fig, use_container_width=True)
