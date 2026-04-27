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
st.set_page_config(page_title="🔥 NSE AI PRO V9.5 - BACKTEST FIXED", layout="wide")
st_autorefresh(interval=60000, key="refresh")

# IST Time Setup
IST = pytz.timezone('Asia/Kolkata')
current_time = datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')

st.title("🚀 NSE AI PRO V9.5 - ULTIMATE TRACKER")
st.write(f"🕒 **Current Market Sync (IST):** {current_time}")
st.markdown("---")

# =============================
# STOCK LIST
# =============================
stocks = [
    "HDFCBANK", "ICICIBANK", "SBIN", "AXISBANK", "KOTAKBANK", "BAJFINANCE", "BAJAJFINSV", "INDUSINDBK",
    "TCS", "INFY", "HCLTECH", "WIPRO", "TECHM", "LTIM",
    "TATAMOTORS", "M&M", "MARUTI", "BAJAJ-AUTO", "EICHERMOT", "HEROMOTOCO",
    "RELIANCE", "NTPC", "POWERGRID", "ONGC", "BPCL", "ADANIGREEN",
    "ITC", "HINDUNILVR", "BRITANNIA", "NESTLEIND", "VBL", "ASIANPAINT",
    "TATASTEEL", "JSWSTEEL", "HINDALCO", "COALINDIA",
    "SUNPHARMA", "DRREDDY", "CIPLA", "DIVISLAB", "APOLLOHOSP",
    "LT", "ULTRACEMCO", "GRASIM", "ADANIPORTS", "BHARTIARTL"
]

# =============================
# CORE FUNCTIONS
# =============================
def get_data(stock, period="2d", interval="15m"):
    try:
        df = yf.Ticker(stock + ".NS").history(period=period, interval=interval)
        return df.dropna() if df is not None and not df.empty else None
    except: return None

def add_indicators(df):
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))
    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
    return df

def get_smart_alerts(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]
    avg_vol = df['Volume'].rolling(20).mean().iloc[-1]
    alerts = []
    if last['Volume'] > avg_vol * 2.5: alerts.append("🐋 BIG FISH")
    if prev['RSI'] < 30 and last['RSI'] > 30: alerts.append("🔄 BULLISH REV")
    elif prev['RSI'] > 70 and last['RSI'] < 70: alerts.append("🔄 BEARISH REV")
    return " | ".join(alerts) if alerts else "Normal"

def calculate_ai_score(df_slice):
    score = 0
    last = df_slice.iloc[-1]
    if last['EMA20'] > last['EMA50']: score += 20
    if 40 < last['RSI'] < 70: score += 20
    if last['Volume'] > df_slice['Volume'].rolling(20).mean().iloc[-1]: score += 20
    if last['Close'] > last['VWAP']: score += 20
    if last['MACD'] > last['Signal_Line']: score += 20
    return score

def get_signal(score, last_close, last_vwap):
    if score >= 80 and last_close > last_vwap: return "🚀 STRONG BUY"
    elif score <= 30 and last_close < last_vwap: return "💀 STRONG SELL"
    elif score >= 60: return "BUY"
    elif score <= 40: return "SELL"
    else: return "WAIT"

# =============================
# UI - LIVE SCAN & BACKTEST TABS
# =============================
tab1, tab2 = st.tabs(["🔍 LIVE SCANNER", "📊 30-DAY BACKTEST REPORT"])

with tab1:
    if st.button("🔍 SCAN ALL SECTORS LIVE"):
        data_results = []
        with st.spinner("Analyzing Market..."):
            for s in stocks:
                df = get_data(s)
                if df is not None:
                    df = add_indicators(df)
                    score = calculate_ai_score(df)
                    sig = get_signal(score, df['Close'].iloc[-1], df['VWAP'].iloc[-1])
                    smart_alert = get_smart_alerts(df)
                    curr_price = round(df['Close'].iloc[-1], 2)
                    last_time = df.index[-1].astimezone(IST).strftime('%H:%M')
                    
                    if "BUY" in sig:
                        sl, target = round(curr_price * 0.99, 2), round(curr_price * 1.02, 2)
                    elif "SELL" in sig:
                        sl, target = round(curr_price * 1.01, 2), round(curr_price * 0.98, 2)
                    else: sl = target = 0
                    
                    data_results.append({
                        "STOCK": s, "TIME": last_time, "PRICE": curr_price, 
                        "SIGNAL": sig, "SMART ALERT": smart_alert, 
                        "STOPLOSS": sl, "TARGET": target
                    })
        if data_results:
            res_df = pd.DataFrame(data_results)
            st.table(res_df)

with tab2:
    st.info("గత 30 రోజుల్లో మీ స్ట్రాటజీ ప్రకారం వచ్చిన పక్కా ఎంట్రీ పాయింట్స్ ఇక్కడ చూడవచ్చు.")
    if st.button("📈 RUN 30-DAY HISTORICAL BACKTEST"):
        bt_logs = []
        with st.spinner("Backtesting last 30 days data..."):
            for s in stocks:
                df_bt = get_data(s, period="1mo", interval="15m")
                if df_bt is not None and len(df_bt) > 50:
                    df_bt = add_indicators(df_bt)
                    for i in range(50, len(df_bt)):
                        score = calculate_ai_score(df_bt.iloc[:i+1])
                        if score >= 80: # Strong Buy Alert
                            sig_dt = df_bt.index[i].astimezone(IST).strftime('%Y-%m-%d %H:%M')
                            bt_logs.append({
                                "DATE & TIME": sig_dt, 
                                "STOCK": s, 
                                "ENTRY PRICE": round(df_bt.iloc[i]['Close'], 2), 
                                "SIGNAL": "🚀 STRONG BUY"
                            })
        if bt_logs:
            st.dataframe(pd.DataFrame(bt_logs), use_container_width=True)
        else:
            st.warning("గత 30 రోజుల్లో ఈ స్ట్రాటజీ ప్రకారం ఎంట్రీలు ఏవీ దొరకలేదు.")

# =============================
# CHART SECTION
# =============================
st.markdown("---")
selected = st.selectbox("Select stock to view Chart:", stocks)
chart_df = get_data(selected, period="5d", interval="15m")
if chart_df is not None:
    chart_df = add_indicators(chart_df)
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=chart_df.index, open=chart_df['Open'], high=chart_df['High'], low=chart_df['Low'], close=chart_df['Close'], name="Price"))
    fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df['VWAP'], line=dict(color='orange', width=1.5), name="VWAP"))
    fig.update_layout(title=f"{selected} Analysis", template="plotly_dark", xaxis_rangeslider_visible=False, height=600)
    st.plotly_chart(fig, use_container_width=True)
