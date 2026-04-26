import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="NSE AI PRO V23 SMART", layout="wide")
st.title("🚀 NSE AI PRO V23 - Smart Money & Exit Tracker")

st_autorefresh(interval=60000, key="refresh")

# =============================
# SECTOR DATA
# =============================
sectors = {
    "NIFTY 50": ["RELIANCE", "HDFCBANK", "ICICIBANK", "INFY", "TCS", "SBIN", "BHARTIARTL", "ITC", "HINDUNILVR", "LT"],
    "BANK NIFTY": ["SBIN", "HDFCBANK", "ICICIBANK", "AXISBANK", "KOTAKBANK", "INDUSINDBK", "PNB", "FEDERALBNK", "IDFCFIRSTB"]
}

st.sidebar.header("⚙️ Settings")
sel_sector = st.sidebar.selectbox("Sector", list(sectors.keys()))
stock = st.sidebar.selectbox("Stock", sectors[sel_sector])
interval = st.sidebar.selectbox("Timeframe", ["5m", "15m", "1h"])

# =============================
# DATA LOAD
# =============================
@st.cache_data(ttl=60)
def load_data(symbol, interval):
    df = yf.Ticker(f"{symbol}.NS").history(period="5d", interval=interval)
    if not df.empty:
        df.index = df.index.tz_localize(None)
    return df

df = load_data(stock, interval)

# =============================
# SMART INDICATORS (Big Player Logic)
# =============================
# 1. EMAs & VWAP
df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
df['Date'] = df.index.date
df['VWAP'] = ( ( (df['High']+df['Low']+df['Close'])/3 ) * df['Volume'] ).groupby(df['Date']).cumsum() / df['Volume'].groupby(df['Date']).cumsum()

# 2. Big Player Entry (Volume Spike > 2x of average)
df['Vol_Avg'] = df['Volume'].rolling(window=20).mean()
df['Big_Entry'] = (df['Volume'] > df['Vol_Avg'] * 2)

# 3. Stop Loss / Exit Logic (ATR based SL)
df['TR'] = pd.concat([df['High']-df['Low'], abs(df['High']-df['Close'].shift()), abs(df['Low']-df['Close'].shift())], axis=1).max(axis=1)
df['ATR'] = df['TR'].rolling(window=14).mean()
df['Long_SL'] = df['Close'] - (df['ATR'] * 1.5) # Dynamic Stop Loss

# =============================
# SIGNAL STATUS
# =============================
last = df.iloc[-1]
prev = df.iloc[-2]

status = "WAITING"
color = "white"
msg = "Market is sideways."

# BUY Logic + Big Player Check
if last['Close'] > last['VWAP'] and last['EMA20'] > last['EMA50']:
    status = "STRONG BUY"
    color = "#00ff00"
    if last['Big_Entry']:
        msg = "🔥 BIG PLAYER DETECTED! High Volume Breakout."
    else:
        msg = "Trend is Bullish. Follow VWAP."

# SELL/EXIT Logic
elif last['Close'] < last['VWAP'] and last['EMA20'] < last['EMA50']:
    status = "STRONG SELL"
    color = "#ff4b4b"
    msg = "Trend is Bearish. Exit Longs."

# Reversal Detection (Exit)
if prev['Close'] > prev['EMA20'] and last['Close'] < last['EMA20']:
    msg = "⚠️ WARNING: Reversal Started. Consider Exiting."

# =============================
# UI DISPLAY
# =============================
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Price", f"₹{last['Close']:.2f}")
with c2:
    st.markdown(f"<h3 style='color:{color}'>{status}</h3>", unsafe_allow_html=True)
with c3:
    st.warning(msg) if "WARNING" in msg else st.info(msg)

st.write(f"🛑 **Recommended Stop Loss (Trailing):** ₹{last['Long_SL']:.2f}")

# =============================
# CHART
# =============================
fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.8, 0.2], vertical_spacing=0.02)

fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Price"), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['VWAP'], name="VWAP", line=dict(color='cyan', width=2)), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['Long_SL'], name="Dynamic SL", line=dict(color='red', dash='dot')), row=1, col=1)

# Highlight Big Player Entry Points
big_entries = df[df['Big_Entry']]
fig.add_trace(go.Scatter(x=big_entries.index, y=big_entries['Close'], mode='markers', marker=dict(symbol='triangle-up', size=12, color='lime'), name="Smart Money Entry"), row=1, col=1)

fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name="Volume", marker_color='gray'), row=2, col=1)

fig.update_layout(height=700, template="plotly_dark", xaxis_rangeslider_visible=False)
st.plotly_chart(fig, use_container_width=True)
