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
st.set_page_config(page_title="🔥 NSE AI PRO V9.1 - FIXED", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone('Asia/Kolkata')
current_time = datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')

st.title("🚀 NSE AI PRO V9.1 - SMART MONEY & BACKTESTER")
st.write(f"🕒 **Current Sync Time (IST):** {current_time}")
st.markdown("---")

# =============================
# STOCK LIST
# =============================
stocks = [
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "AXISBANK", 
    "TATAMOTORS", "M&M", "MARUTI", "ITC", "HINDUNILVR", "TATASTEEL", 
    "JSWSTEEL", "SUNPHARMA", "CIPLA", "LT", "BHARTIARTL", "BAJFINANCE"
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
# UI SCANNER & BACKTEST
# =============================
tab1, tab2 = st.tabs(["🔍 LIVE SCANNER", "📊 BACKTEST REPORT"])

with tab1:
    if st.button("🔍 RUN LIVE SCAN"):
        data_results = []
        with st.spinner("Analyzing Market..."):
            for s in stocks:
                df = get_data(s)
                if df is not None:
                    df = add_indicators(df)
                    score = calculate_ai_score(df)
                    sig = get_signal(df, score)
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
            st.table(pd.DataFrame(data_results))

with tab2:
    if st.button("📈 START 30-DAY BACKTEST"):
        bt_full_logs = []
        with st.spinner("Checking last 30 days..."):
            for s in stocks:
                df_bt = get_data(s, period="1mo", interval="15m")
                if df_bt is not None and len(df_bt) > 50:
                    df_bt = add_indicators(df_bt)
                    for i in range(50, len(df_bt)-1):
                        score = calculate_ai_score(df_bt.iloc[:i+1])
                        if score >= 80: # Strong Buy Logic
                            sig_time = df_bt.index[i].astimezone(IST).strftime('%Y-%m-%d %H:%M')
                            bt_full_logs.append({
                                "DATE & TIME": sig_time, "STOCK": s, 
                                "PRICE": round(df_bt.iloc[i]['Close'], 2), "SIGNAL": "STRONG BUY"
                            })
        if bt_full_logs:
            st.subheader("📅 Backtest Log (Historical Entry Points)")
            st.dataframe(pd.DataFrame(bt_full_logs), use_container_width=True)

# =============================
# CHART SECTION
# =============================
st.markdown("---")
selected = st.selectbox("Select Stock for Chart:", stocks)
chart_df = get_data(selected, period="5d", interval="15m")
if chart_df is not None:
    chart_df = add_indicators(chart_df)
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=chart_df.index, open=chart_df['Open'], high=chart_df['High'], low=chart_df['Low'], close=chart_df['Close'], name="Price"))
    fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df['VWAP'], line=dict(color='orange', width=1.5), name="VWAP"))
    fig.update_layout(title=f"{selected} Analysis", template="plotly_dark", xaxis_rangeslider_visible=False, height=600)
    st.plotly_chart(fig, use_container_width=True)
