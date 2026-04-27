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
st.set_page_config(page_title="🔥 NSE AI PRO V9.7", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone('Asia/Kolkata')
current_time = datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')

st.title("🚀 NSE AI PRO V9.7 - ULTIMATE TRACKER")
st.write(f"🕒 **Current Market Sync (IST):** {current_time}")
st.markdown("---")

# =============================
# STOCK LIST
# =============================
stocks = {
    "HDFCBANK":"Banking","ICICIBANK":"Banking","SBIN":"Banking",
    "RELIANCE":"Oil & Gas","TCS":"IT","INFY":"IT",
    "ITC":"FMCG","LT":"Infra","BHARTIARTL":"Telecom"
}

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
# UI - LIVE & BACKTEST
# =============================
tab1, tab2 = st.tabs(["🔍 LIVE SCANNER", "📊 BACKTEST REPORT"])

with tab1:
    if st.button("🔍 SCAN LIVE"):
        results = []
        for s, sector in stocks.items():
            df = get_data(s)
            if df is not None:
                df = add_indicators(df)
                score = calculate_ai_score(df)
                sig = get_signal(score, df['Close'].iloc[-1], df['VWAP'].iloc[-1])
                curr_price = round(df['Close'].iloc[-1], 2)
                last_time = df.index[-1].astimezone(IST).strftime('%H:%M')
                results.append({"STOCK":s,"SECTOR":sector,"TIME":last_time,"PRICE":curr_price,"SIGNAL":sig})
        if results: st.table(pd.DataFrame(results))

with tab2:
    bt_date = st.date_input("📅 Select Backtest Date", datetime.now(IST).date())
    if st.button("📈 RUN BACKTEST"):
        bt_logs = []
        for s, sector in stocks.items():
            df_bt = get_data(s, period="1mo", interval="15m")
            if df_bt is not None and len(df_bt) > 50:
                df_bt = add_indicators(df_bt)
                df_bt = df_bt[df_bt.index.date == bt_date]
                for i in range(50, len(df_bt)):
                    score = calculate_ai_score(df_bt.iloc[:i+1])
                    sig = get_signal(score, df_bt.iloc[i]['Close'], df_bt.iloc[i]['VWAP'])
                    sig_dt = df_bt.index[i].astimezone(IST).strftime('%Y-%m-%d %H:%M')
                    bt_logs.append({
                        "DATE & TIME": sig_dt,
                        "STOCK": s,
                        "SECTOR": sector,
                        "ENTRY PRICE": round(df_bt.iloc[i]['Close'], 2),
                        "SIGNAL": sig
                    })
        if bt_logs:
            df_logs = pd.DataFrame(bt_logs).sort_values(by="DATE & TIME")
            st.dataframe(df_logs, use_container_width=True)
            df_logs.to_csv("signals_backtest.csv", index=False)
            st.success("✅ Backtest logs saved to signals_backtest.csv")
        else: st.warning("ఈ తేదీకి signals ఏవీ దొరకలేదు.")

# =============================
# CHART SECTION
# =============================
st.markdown("---")
selected = st.selectbox("Select stock to view Chart:", list(stocks.keys()))
chart_df = get_data(selected, period="5d", interval="15m")
if chart_df is not None:
    chart_df = add_indicators(chart_df)
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=chart_df.index, open=chart_df['Open'], high=chart_df['High'], low=chart_df['Low'], close=chart_df['Close'], name="Price"))
    fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df['VWAP'], line=dict(color='orange', width=1.5), name="VWAP"))
    fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df['EMA20'], line=dict(color='green', width=1), name="EMA20"))
    fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df['EMA50'], line=dict(color='red', width=1), name="EMA50"))
    fig.update_layout(title=f"{selected} Analysis", template="plotly_dark", xaxis_rangeslider_visible=False, height=600)
    st.plotly_chart(fig, use_container_width=True)
