import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG & REFRESH
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V8.1 - SMART MONEY", layout="wide")
st_autorefresh(interval=60000, key="refresh")

st.title("🚀 NSE AI PRO V8.1 - SMART MONEY TRACKER")
st.markdown("---")

# =============================
# STOCK LIST
# =============================
stocks = [
    "RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","ITC","LT",
    "AXISBANK","BHARTIARTL","KOTAKBANK","MARUTI","M&M","TATAMOTORS",
    "SUNPHARMA","DRREDDY","CIPLA","HCLTECH","WIPRO","TECHM",
    "JSWSTEEL","TATASTEEL","HINDALCO"
]

# =============================
# DATA & INDICATORS
# =============================
def get_data(stock):
    try:
        df = yf.Ticker(stock + ".NS").history(period="5d", interval="15m")
        return df.dropna() if df is not None and not df.empty else None
    except: return None

def add_indicators(df):
    # EMA
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))
    # VWAP
    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
    # MACD
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
    return df

# =============================
# SMART ALERTS LOGIC
# =============================
def get_smart_alerts(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]
    avg_vol = df['Volume'].rolling(20).mean().iloc[-1]
    
    alerts = []
    # Big Player Entry (2x Avg Volume)
    if last['Volume'] > avg_vol * 2:
        alerts.append("🐋 BIG FISH")
    # Reversal Detection
    if prev['RSI'] < 30 and last['RSI'] > 30:
        alerts.append("🔄 BULLISH REV")
    elif prev['RSI'] > 70 and last['RSI'] < 70:
        alerts.append("🔄 BEARISH REV")
        
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
# UI SCANNER SECTION
# =============================
if st.button("🔍 RUN SMART SCANNER"):
    data_results = []
    with st.spinner("Analyzing Smart Money Flow..."):
        for s in stocks:
            df = get_data(s)
            if df is not None:
                df = add_indicators(df)
                score = calculate_ai_score(df)
                sig = get_signal(df, score)
                smart_alert = get_smart_alerts(df)
                curr_price = round(df['Close'].iloc[-1], 2)
                
                # Correct SL/Target for Buy and Sell
                if "BUY" in sig:
                    sl, target = round(curr_price * 0.99, 2), round(curr_price * 1.02, 2)
                elif "SELL" in sig:
                    sl, target = round(curr_price * 1.01, 2), round(curr_price * 0.98, 2)
                else: sl = target = 0
                
                data_results.append({
                    "STOCK": s, "PRICE": curr_price, "SIGNAL": sig,
                    "SMART ALERT": smart_alert, "AI SCORE": f"{score}%",
                    "ENTRY": curr_price, "STOPLOSS": sl, "TARGET": target,
                    "RSI": round(df['RSI'].iloc[-1], 1)
                })

    if data_results:
        res_df = pd.DataFrame(data_results)
        st.subheader("📊 SMART MONEY SIGNALS")
        
        # Style function with Error Protection
        def style_alerts(val):
            if "BIG FISH" in val: return 'background-color: #4B0082; color: white; font-weight: bold'
            if "REV" in val: return 'background-color: #FFD700; color: black; font-weight: bold'
            return ''

        # Display table with fixed styling function
        try:
            st.table(res_df[["STOCK", "PRICE", "SIGNAL", "SMART ALERT", "STOPLOSS", "TARGET"]].style.map(style_alerts, subset=['SMART ALERT']))
        except AttributeError:
            st.table(res_df[["STOCK", "PRICE", "SIGNAL", "SMART ALERT", "STOPLOSS", "TARGET"]].style.applymap(style_alerts, subset=['SMART ALERT']))
        
        with st.expander("🔍 Detailed Technical Breakdown"):
            st.dataframe(res_df[["STOCK", "AI SCORE", "RSI", "SMART ALERT"]], use_container_width=True)

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
    fig.update_layout(title=f"{selected} Analysis", template="plotly_dark", xaxis_rangeslider_visible=False, height=600)
    st.plotly_chart(fig, use_container_width=True)
