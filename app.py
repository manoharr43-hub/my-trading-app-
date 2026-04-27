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
st.set_page_config(page_title="🔥 NSE AI PRO V9.7 - FIXED", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone('Asia/Kolkata')
current_time = datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')

st.title("🚀 NSE AI PRO V9.7 - ULTIMATE TRACKER")
st.write(f"🕒 **Current Market Sync (IST):** {current_time}")
st.markdown("---")

# =============================
# STOCK LIST
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
# SAFE DATA FUNCTION
# =============================
@st.cache_data(ttl=60)
def get_data(stock, period="2d", interval="15m"):
    try:
        df = yf.Ticker(stock + ".NS").history(period=period, interval=interval)
        if df is None or df.empty or len(df) < 20:
            return None
        return df.dropna()
    except:
        return None

# =============================
# INDICATORS
# =============================
def add_indicators(df):
    df = df.copy()
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    delta = df['Close'].diff()
    gain = (delta.clip(lower=0)).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))

    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-9)

    exp1 = df['Close'].ewm(span=12).mean()
    exp2 = df['Close'].ewm(span=26).mean()
    df['MACD'] = exp1 - exp2
    df['Signal_Line'] = df['MACD'].ewm(span=9).mean()
    return df

# =============================
# ALERTS
# =============================
def get_smart_alerts(df):
    try:
        last = df.iloc[-1]
        prev = df.iloc[-2]
        avg_vol = df['Volume'].rolling(20).mean().iloc[-1]
        alerts = []
        if last['Volume'] > avg_vol * 2.5:
            alerts.append("🐋 BIG FISH")
        if prev['RSI'] < 30 and last['RSI'] > 30:
            alerts.append("🔄 BULLISH REV")
        elif prev['RSI'] > 70 and last['RSI'] < 70:
            alerts.append("🔄 BEARISH REV")
        return " | ".join(alerts) if alerts else "Normal"
    except:
        return "Normal"

# =============================
# AI SCORE
# =============================
def calculate_ai_score(df):
    try:
        last = df.iloc[-1]
        score = 0
        if last['EMA20'] > last['EMA50']: score += 20
        if 40 < last['RSI'] < 70: score += 20
        if last['Volume'] > df['Volume'].rolling(20).mean().iloc[-1]: score += 20
        if last['Close'] > last['VWAP']: score += 20
        if last['MACD'] > last['Signal_Line']: score += 20
        return score
    except:
        return 0

# =============================
# SIGNAL
# =============================
def get_signal(score, close, vwap):
    if score >= 80 and close > vwap:
        return "🚀 STRONG BUY"
    elif score <= 30 and close < vwap:
        return "💀 STRONG SELL"
    elif score >= 60:
        return "BUY"
    elif score <= 40:
        return "SELL"
    else:
        return "WAIT"

# =============================
# TABS
# =============================
tab1, tab2 = st.tabs(["🔍 LIVE SCANNER", "📊 BACKTEST"])

# =============================
# LIVE SCANNER
# =============================
with tab1:
    if st.button("🔍 SCAN ALL SECTORS LIVE", key="scan_btn"):
        st.write("⏳ Scanning started...")
        results = []
        for s in stocks:
            try:
                df = get_data(s)
                if df is None:
                    continue
                df = add_indicators(df)
                price = round(df['Close'].iloc[-1], 2)
                vwap = df['VWAP'].iloc[-1]
                score = calculate_ai_score(df)
                signal = get_signal(score, price, vwap)
                alert = get_smart_alerts(df)
                last_time = df.index[-1]
                try:
                    last_time = last_time.tz_convert(IST)
                except:
                    pass
                last_time = last_time.strftime('%H:%M')
                if "BUY" in signal:
                    sl, target = round(price * 0.99, 2), round(price * 1.02, 2)
                elif "SELL" in signal:
                    sl, target = round(price * 1.01, 2), round(price * 0.98, 2)
                else:
                    sl = target = 0
                results.append({
                    "STOCK": s,
                    "TIME": last_time,
                    "PRICE": price,
                    "SIGNAL": signal,
                    "ALERT": alert,
                    "SL": sl,
                    "TARGET": target
                })
            except:
                continue
        if results:
            st.dataframe(pd.DataFrame(results), use_container_width=True)
        else:
            st.warning("⚠️ No data found / API issue")

# =============================
# BACKTEST
# =============================
with tab2:
    if st.button("📈 RUN BACKTEST", key="backtest_btn"):
        logs = []
        for s in stocks:
            try:
                df = get_data(s, period="1mo", interval="15m")
                if df is None or len(df) < 50:
                    continue
                df = add_indicators(df)
                for i in range(50, len(df)):
                    score = calculate_ai_score(df.iloc[:i+1])
                    if score >= 80:
                        logs.append({
                            "DATE": df.index[i].strftime('%Y-%m-%d'),
                            "TIME": df.index[i].strftime('%H:%M'),
                            "STOCK": s,
                            "PRICE": round(df.iloc[i]['Close'], 2),
                            "SIGNAL": "🚀 STRONG BUY"
                        })
            except:
                continue
        if logs:
            st.dataframe(pd.DataFrame(logs), use_container_width=True)
        else:
            st.warning("No signals found")

# =============================
# CHART
# =============================
st.markdown("---")
selected = st.selectbox("Select Stock:", stocks)
df = get_data(selected, period="5d", interval="15m")
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
else:
    st.warning("Chart data not available")
