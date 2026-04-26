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
    try:
        df = yf.Ticker(f"{symbol}.NS").history(period="5d", interval=interval)
        if not df.empty:
            df.index = df.index.tz_localize(None)
        return df
    except:
        return pd.DataFrame()

df = load_data(stock, interval)

if df.empty:
    st.error("Market data fetch cheyadamlo error vachindi. Please check symbol.")
    st.stop()

# =============================
# SMART INDICATORS
# =============================
df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
df['Date'] = df.index.date
df['VWAP'] = ( ( (df['High']+df['Low']+df['Close'])/3 ) * df['Volume'] ).groupby(df['Date']).cumsum() / df['Volume'].groupby(df['Date']).cumsum()

# Big Player Entry (Volume Spike)
df['Vol_Avg'] = df['Volume'].rolling(window=20).mean()
df['Big_Entry'] = (df['Volume'] > df['Vol_Avg'] * 2.5)

# ATR based SL
df['TR'] = pd.concat([df['High']-df['Low'], abs(df['High']-df['Close'].shift()), abs(df['Low']-df['Close'].shift())], axis=1).max(axis=1)
df['ATR'] = df['TR'].rolling(window=14).mean()
df['Long_SL'] = df['Close'] - (df['ATR'] * 1.5)

# =============================
# SIGNAL STATUS LOGIC
# =============================
last = df.iloc[-1]
prev = df.iloc[-2]
status = "NEUTRAL"
color = "white"
msg = "Market is in range."

if last['Close'] > last['VWAP'] and last['EMA20'] > last['EMA50']:
    status = "STRONG BUY"
    color = "#00ff00"
    msg = "🔥 BIG PLAYER ENTRY DETECTED!" if last['Big_Entry'] else "Trend is Bullish."
elif last['Close'] < last['VWAP'] and last['EMA20'] < last['EMA50']:
    status = "STRONG SELL"
    color = "#ff4b4b"
    msg = "📉 TREND IS BEARISH. EXIT LONGS."

# Reversal Warning
if prev['Close'] > prev['EMA20'] and last['Close'] < last['EMA20']:
    msg = "⚠️ REVERSAL ALERT: Price closing below EMA20!"

# =============================
# UI DISPLAY (Fixed DeltaGenerator Issue)
# =============================
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Price", f"₹{last['Close']:.2f}")
with c2:
    st.markdown(f"<h2 style='color:{color}; text-align:center;'>{status}</h2>", unsafe_allow_html=True)
with c3:
    if "REVERSAL" in msg or "EXIT" in msg:
        st.warning(msg)
    elif "BIG PLAYER" in msg:
        st.success(msg)
    else:
        st.info(msg)

st.divider()
st.subheader(f"🛑 Recommended Stop Loss (Trailing): ₹{last['Long_SL']:.2f}")

# =============================
# SMART CHART
# =============================
fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.8, 0.2], vertical_spacing=0.02)
fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Price"), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['VWAP'], name="VWAP", line=dict(color='cyan', width=2)), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['EMA20'], name="EMA20", line=dict(color='yellow', width=1)), row=1, col=1)

# Big Player Markers
big_entries = df[df['Big_Entry']]
fig.add_trace(go.Scatter(x=big_entries.index, y=big_entries['Close'], mode='markers', marker=dict(symbol='star', size=12, color='lime'), name="Smart Money Entry"), row=1, col=1)

fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name="Volume", marker_color='gray'), row=2, col=1)
fig.update_layout(height=700, template="plotly_dark", xaxis_rangeslider_visible=False)
st.plotly_chart(fig, use_container_width=True)
