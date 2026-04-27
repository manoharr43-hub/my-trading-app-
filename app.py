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
st.set_page_config(page_title="🔥 NSE AI PRO V8.5 - SECTOR EDITION", layout="wide")
st_autorefresh(interval=60000, key="refresh")

# IST Time Setup
IST = pytz.timezone('Asia/Kolkata')
current_time = datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')

st.title("🚀 NSE AI PRO V8.5 - MULTI-SECTOR TRACKER")
st.write(f"🕒 **Last Market Sync (IST):** {current_time}")
st.markdown("---")

# =============================
# ALL SECTOR STOCK LIST
# =============================
stocks = [
    # Banking & Finance
    "HDFCBANK", "ICICIBANK", "SBIN", "AXISBANK", "KOTAKBANK", "BAJFINANCE", "BAJAJFINSV", "INDUSINDBK",
    # IT (Tech)
    "TCS", "INFY", "HCLTECH", "WIPRO", "TECHM", "LTIM",
    # Automobile
    "TATAMOTORS", "M&M", "MARUTI", "BAJAJ-AUTO", "EICHERMOT", "HEROMOTOCO",
    # Energy & Power
    "RELIANCE", "NTPC", "POWERGRID", "ONGC", "BPCL", "ADANIGREEN",
    # FMCG & Consumer
    "ITC", "HINDUNILVR", "BRITANNIA", "NESTLEIND", "VBL", "ASIANPAINT",
    # Metals & Mining
    "TATASTEEL", "JSWSTEEL", "HINDALCO", "COALINDIA",
    # Pharma & Healthcare
    "SUNPHARMA", "DRREDDY", "CIPLA", "DIVISLAB", "APOLLOHOSP",
    # Infrastructure & Others
    "LT", "ULTRACEMCO", "GRASIM", "ADANIPORTS", "BHARTIARTL"
]

# =============================
# DATA & ANALYSIS FUNCTIONS
# =============================
def get_data(stock):
    try:
        df = yf.Ticker(stock + ".NS").history(period="2d", interval="15m")
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

def calculate_ai_score(df):
    score = 0
    last = df.iloc[-1]
    if last['EMA20'] > last['EMA50']: score += 20
    if 40 < last['RSI'] < 70: score += 20
    if last['Volume'] > df['Volume'].rolling(20).mean().iloc[-1]: score += 20
    if last['Close'] > last['VWAP']: score += 20
    if last['MACD'] > last['Signal_Line']: score += 20
    return score

def get_signal(df, score):
    last = df.iloc[-1]
    if score >= 80 and last['Close'] > last['VWAP']: return "🚀 STRONG BUY"
    elif score <= 30 and last['Close'] < last['VWAP']: return "💀 STRONG SELL"
    elif score >= 60: return "BUY"
    elif score <= 40: return "SELL"
    else: return "WAIT"

# =============================
# MAIN UI SCANNER
# =============================
if st.button("🔍 SCAN ALL SECTORS"):
    data_results = []
    with st.spinner("Analyzing 40+ Stocks Across All Sectors..."):
        for s in stocks:
            df = get_data(s)
            if df is not None:
                df = add_indicators(df)
                score = calculate_ai_score(df)
                sig = get_signal(df, score)
                smart_alert = get_smart_alerts(df)
                curr_price = round(df['Close'].iloc[-1], 2)
                last_candle_time = df.index[-1].astimezone(IST).strftime('%H:%M')
                
                if "BUY" in sig:
                    sl, target = round(curr_price * 0.99, 2), round(curr_price * 1.02, 2)
                elif "SELL" in sig:
                    sl, target = round(curr_price * 1.01, 2), round(curr_price * 0.98, 2)
                else: sl = target = 0
                
                data_results.append({
                    "STOCK": s, "TIME": last_candle_time, "PRICE": curr_price, 
                    "SIGNAL": sig, "SMART ALERT": smart_alert, 
                    "AI SCORE": f"{score}%", "STOPLOSS": sl, "TARGET": target
                })

    if data_results:
        res_df = pd.DataFrame(data_results)
        st.subheader("📊 REAL-TIME MARKET SIGNALS")
        
        def style_alerts(val):
            if "BIG FISH" in val: return 'background-color: #4B0082; color: white; font-weight: bold'
            if "REV" in val: return 'background-color: #FFD700; color: black; font-weight: bold'
            return ''

        # Display Result Table
        try:
            st.table(res_df[["STOCK", "TIME", "PRICE", "SIGNAL", "SMART ALERT", "STOPLOSS", "TARGET"]].style.map(style_alerts, subset=['SMART ALERT']))
        except AttributeError:
            st.table(res_df[["STOCK", "TIME", "PRICE", "SIGNAL", "SMART ALERT", "STOPLOSS", "TARGET"]].style.applymap(style_alerts, subset=['SMART ALERT']))
        
        with st.expander("🔍 Detailed Sector Analysis & Scores"):
            st.dataframe(res_df, use_container_width=True)

# =============================
# CHART SECTION
# =============================
st.markdown("---")
selected = st.selectbox("Select stock to view Chart:", stocks)
chart_df = get_data(selected)
if chart_df is not None:
    chart_df = add_indicators(chart_df)
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=chart_df.index, open=chart_df['Open'], high=chart_df['High'], low=chart_df['Low'], close=chart_df['Close'], name="Price"))
    fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df['VWAP'], line=dict(color='orange', width=1.5), name="VWAP"))
    fig.update_layout(title=f"{selected} Advanced Analysis", template="plotly_dark", xaxis_rangeslider_visible=False, height=600)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("పైన ఉన్న బటన్ నొక్కి డేటాను స్కాన్ చేయండి.")
