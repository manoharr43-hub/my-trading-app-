import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
import pytz

# =============================
# CONFIG & REFRESH
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V10 - SMART TRACKER", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone('Asia/Kolkata')
current_time = datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')

st.title("🚀 NSE AI PRO V10 - UPGRADED DASHBOARD")
st.write(f"🕒 **Market Sync (IST):** {current_time}")
st.markdown("---")

# =============================
# STOCK LIST (UNCHANGED)
# =============================
stocks = [
    "HDFCBANK","ICICIBANK","SBIN","AXISBANK","KOTAKBANK","BAJFINANCE","BAJAJFINSV","INDUSINDBK",
    "TCS","INFY","HCLTECH","WIPRO","TECHM","LTIM",
    "TATAMOTORS","M&M","MARUTI","BAJAJ-AUTO","EICHERMOT","HEROMOTOCO",
    "RELIANCE","NTPC","POWERGRID","ONGC","BPCL","ADANIGREEN",
    "ITC","HINDUNILVR","BRITANNIA","NESTLEIND","VBL","ASIANPAINT",
    "TATASTEEL","JSWSTEEL","HINDALCO","COALINDIA",
    "SUNPHARMA","DRREDDY","CIPLA","DIVISLAB","APOLLOHOSP",
    "LT","ULTRACEMCO","GRASIM","ADANIPORTS","BHARTIARTL"
]

# =============================
# DATA FUNCTION (FASTER)
# =============================
@st.cache_data(ttl=60)
def get_data(stock, period="2d", interval="15m"):
    try:
        df = yf.Ticker(stock + ".NS").history(period=period, interval=interval)
        if df is None or df.empty:
            return None
        return df.dropna()
    except:
        return None

# =============================
# INDICATORS (IMPROVED)
# =============================
def add_indicators(df):
    df = df.copy()

    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    # RSI (more accurate)
    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/14, min_periods=14).mean()
    avg_loss = loss.ewm(alpha=1/14, min_periods=14).mean()
    rs = avg_gain / (avg_loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))

    # VWAP (daily reset fix)
    df['CumVol'] = df['Volume'].groupby(df.index.date).cumsum()
    df['CumPV'] = (df['Close'] * df['Volume']).groupby(df.index.date).cumsum()
    df['VWAP'] = df['CumPV'] / df['CumVol']

    # MACD
    exp1 = df['Close'].ewm(span=12).mean()
    exp2 = df['Close'].ewm(span=26).mean()
    df['MACD'] = exp1 - exp2
    df['Signal_Line'] = df['MACD'].ewm(span=9).mean()

    # Volume spike
    df['Vol_Avg'] = df['Volume'].rolling(20).mean()
    df['Big_Player'] = df['Volume'] > (df['Vol_Avg'] * 2.5)

    return df

# =============================
# ALERTS (UPGRADE)
# =============================
def get_smart_alerts(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]

    alerts = []

    if last['Big_Player']:
        alerts.append("🐋 BIG FISH")

    if prev['RSI'] < 30 and last['RSI'] > 30:
        alerts.append("🔄 BULLISH REV")

    if prev['RSI'] > 70 and last['RSI'] < 70:
        alerts.append("🔄 BEARISH REV")

    return " | ".join(alerts) if alerts else "Normal"

# =============================
# AI SCORE (ENHANCED)
# =============================
def calculate_ai_score(df):
    last = df.iloc[-1]
    score = 0

    if last['EMA20'] > last['EMA50']: score += 20
    if 45 < last['RSI'] < 70: score += 20
    if last['Close'] > last['VWAP']: score += 20
    if last['MACD'] > last['Signal_Line']: score += 20
    if last['Big_Player']: score += 20

    return score

# =============================
# SIGNAL LOGIC (SMART)
# =============================
def get_signal(score, price, vwap):
    if score >= 80 and price > vwap:
        return "🚀 STRONG BUY"
    elif score <= 30 and price < vwap:
        return "💀 STRONG SELL"
    elif score >= 60:
        return "BUY"
    elif score <= 40:
        return "SELL"
    else:
        return "WAIT"

# =============================
# LIVE SCANNER
# =============================
tab1, tab2 = st.tabs(["🔍 LIVE SCANNER", "📊 BACKTEST"])

with tab1:
    if st.button("🔍 SCAN LIVE MARKET"):
        results = []

        with st.spinner("Scanning..."):
            for s in stocks:
                df = get_data(s)
                if df is None or len(df) < 50:
                    continue

                df = add_indicators(df)

                price = round(df['Close'].iloc[-1], 2)
                vwap = df['VWAP'].iloc[-1]

                score = calculate_ai_score(df)
                signal = get_signal(score, price, vwap)
                alert = get_smart_alerts(df)

                # Dynamic SL/Target
                if "BUY" in signal:
                    sl = round(price * 0.99, 2)
                    tgt = round(price * 1.025, 2)
                elif "SELL" in signal:
                    sl = round(price * 1.01, 2)
                    tgt = round(price * 0.975, 2)
                else:
                    sl, tgt = 0, 0

                results.append({
                    "Stock": s,
                    "Price": price,
                    "Signal": signal,
                    "AI Score": score,
                    "Alert": alert,
                    "SL": sl,
                    "Target": tgt
                })

        st.dataframe(pd.DataFrame(results), use_container_width=True)

# =============================
# BACKTEST (FIXED)
# =============================
with tab2:
    if st.button("📊 RUN BACKTEST"):
        logs = []

        with st.spinner("Running..."):
            for s in stocks:
                df = get_data(s, period="1mo", interval="15m")

                if df is None or len(df) < 50:
                    continue

                df = add_indicators(df)

                for i in range(50, len(df)):
                    temp = df.iloc[:i+1]
                    score = calculate_ai_score(temp)

                    if score >= 80:
                        logs.append({
                            "Time": df.index[i].strftime('%Y-%m-%d %H:%M'),
                            "Stock": s,
                            "Price": round(df.iloc[i]['Close'], 2),
                            "Signal": "STRONG BUY"
                        })

        if logs:
            st.dataframe(pd.DataFrame(logs), use_container_width=True)
        else:
            st.warning("No signals found")

# =============================
# CHART
# =============================
st.markdown("---")

stock = st.selectbox("Select Stock", stocks)
df = get_data(stock, period="5d", interval="15m")

if df is not None:
    df = add_indicators(df)

    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close']
    ))

    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['VWAP'],
        name="VWAP"
    ))

    fig.update_layout(template="plotly_dark", height=600)
    st.plotly_chart(fig, use_container_width=True)
