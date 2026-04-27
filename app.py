import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
import pytz

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V9.7", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone('Asia/Kolkata')
current_time = datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')

st.title("🚀 NSE AI PRO V9.7 - LIVE + BACKTEST")
st.write(f"🕒 Market Time (IST): {current_time}")
st.markdown("---")

# =============================
# STOCK LIST
# =============================
stocks = ["HDFCBANK","ICICIBANK","SBIN","RELIANCE","TCS","INFY","ITC","LT","BHARTIARTL"]

# =============================
# DATA FUNCTION
# =============================
def get_data(stock, period="2d", interval="15m"):
    try:
        df = yf.Ticker(stock + ".NS").history(period=period, interval=interval)
        if df is None or df.empty:
            return None
        df = df.dropna()
        df.index = df.index.tz_convert(IST)  # FIXED TIMEZONE
        return df
    except:
        return None

# =============================
# INDICATORS
# =============================
def add_indicators(df):
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))

    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()

    exp1 = df['Close'].ewm(span=12).mean()
    exp2 = df['Close'].ewm(span=26).mean()
    df['MACD'] = exp1 - exp2
    df['Signal_Line'] = df['MACD'].ewm(span=9).mean()

    return df

# =============================
# AI SCORE
# =============================
def calculate_ai_score(df):
    score = 0
    last = df.iloc[-1]

    if last['EMA20'] > last['EMA50']: score += 20
    if 40 < last['RSI'] < 70: score += 20
    if last['Volume'] > df['Volume'].rolling(20).mean().iloc[-1]: score += 20
    if last['Close'] > last['VWAP']: score += 20
    if last['MACD'] > last['Signal_Line']: score += 20

    return score

# =============================
# SIGNAL LOGIC
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
    if st.button("🔍 SCAN LIVE"):
        results = []

        for s in stocks:
            df = get_data(s)

            if df is not None and len(df) > 50:
                df = add_indicators(df)

                score = calculate_ai_score(df)
                sig = get_signal(score, df['Close'].iloc[-1], df['VWAP'].iloc[-1])

                results.append({
                    "Stock": s,
                    "Time": df.index[-1].strftime('%H:%M'),
                    "Price": round(df['Close'].iloc[-1], 2),
                    "Signal": sig
                })

        if results:
            st.dataframe(pd.DataFrame(results), use_container_width=True)
        else:
            st.warning("No data found")

# =============================
# BACKTEST
# =============================
with tab2:
    bt_date = st.date_input("📅 Select Date", datetime.now(IST).date())

    if st.button("📈 RUN BACKTEST"):
        bt_logs = []

        for s in stocks:
            df = get_data(s, period="1mo", interval="15m")

            if df is not None and len(df) > 50:
                df = add_indicators(df)

                # FIXED DATE FILTER
                df_day = df[df.index.date == bt_date]

                if len(df_day) < 50:
                    continue

                for i in range(50, len(df_day)):
                    df_slice = df_day.iloc[:i+1]

                    score = calculate_ai_score(df_slice)
                    sig = get_signal(score, df_day.iloc[i]['Close'], df_day.iloc[i]['VWAP'])

                    bt_logs.append({
                        "Time": df_day.index[i].strftime('%H:%M'),
                        "Stock": s,
                        "Price": round(df_day.iloc[i]['Close'], 2),
                        "Signal": sig
                    })

        if bt_logs:
            st.dataframe(pd.DataFrame(bt_logs), use_container_width=True)
        else:
            st.warning("⚠️ ఈ తేదీకి signals లేవు (No signals for this date)")

# =============================
# CHART
# =============================
st.markdown("---")

selected = st.selectbox("📊 Select Stock", stocks)

df_chart = get_data(selected, period="5d", interval="15m")

if df_chart is not None:
    df_chart = add_indicators(df_chart)

    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df_chart.index,
        open=df_chart['Open'],
        high=df_chart['High'],
        low=df_chart['Low'],
        close=df_chart['Close'],
        name="Price"
    ))

    fig.add_trace(go.Scatter(
        x=df_chart.index,
        y=df_chart['VWAP'],
        name="VWAP",
        line=dict(color='orange')
    ))

    fig.update_layout(
        title=f"{selected} Chart",
        template="plotly_dark",
        height=600,
        xaxis_rangeslider_visible=False
    )

    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Chart data not available")
