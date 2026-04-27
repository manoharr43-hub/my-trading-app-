import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
import pytz

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V10", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone('Asia/Kolkata')
current_time = datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')

st.title("🚀 NSE AI PRO V10 - SMART MONEY SYSTEM")
st.write(f"🕒 Market Time (IST): {current_time}")
st.markdown("---")

# =============================
# LOAD NSE 200 STOCKS
# =============================
@st.cache_data(ttl=86400)
def load_stocks():
    try:
        url = "https://archives.nseindia.com/content/indices/ind_nifty200list.csv"
        df = pd.read_csv(url)
        return df['Symbol'].tolist()
    except:
        return ["RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK"]

stocks = load_stocks()

# =============================
# DATA FETCH
# =============================
def get_data(stock, interval):
    try:
        df = yf.Ticker(stock + ".NS").history(period="5d", interval=interval)
        if df is None or df.empty:
            return None
        df.index = df.index.tz_convert(IST)
        return df.dropna()
    except:
        return None

# =============================
# INDICATORS
# =============================
def add_indicators(df):
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    delta = df['Close'].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))

    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()

    exp1 = df['Close'].ewm(span=12).mean()
    exp2 = df['Close'].ewm(span=26).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9).mean()

    return df

# =============================
# AI SCORE
# =============================
def ai_score(df):
    last = df.iloc[-1]
    score = 0

    if last['EMA20'] > last['EMA50']: score += 20
    if 45 < last['RSI'] < 70: score += 20
    if last['Close'] > last['VWAP']: score += 20
    if last['MACD'] > last['Signal']: score += 20
    if last['Volume'] > df['Volume'].rolling(20).mean().iloc[-1]: score += 20

    return score

# =============================
# SMART MONEY
# =============================
def smart_money(df):
    last = df.iloc[-1]
    avg_vol = df['Volume'].rolling(20).mean().iloc[-1]

    if last['Volume'] > avg_vol * 2 and last['Close'] > last['VWAP']:
        return "🔥 BIG PLAYER"
    return ""

# =============================
# SIGNAL
# =============================
def signal(score):
    if score >= 80: return "🚀 STRONG BUY"
    elif score >= 60: return "BUY"
    elif score <= 30: return "💀 STRONG SELL"
    elif score <= 40: return "SELL"
    else: return "WAIT"

# =============================
# TABS
# =============================
tab1, tab2 = st.tabs(["🔍 LIVE AI SCANNER", "📊 BACKTEST"])

# =============================
# LIVE SCANNER
# =============================
with tab1:

    if st.button("🚀 RUN FULL SCAN"):

        results = []

        for s in stocks[:80]:  # limit for speed

            df5 = get_data(s, "5m")
            df15 = get_data(s, "15m")
            df1h = get_data(s, "1h")

            if df5 is None or df15 is None or df1h is None:
                continue

            df5 = add_indicators(df5)
            df15 = add_indicators(df15)
            df1h = add_indicators(df1h)

            score = (ai_score(df5) + ai_score(df15) + ai_score(df1h)) / 3

            sig = signal(score)
            sm = smart_money(df5)

            last_price = df5['Close'].iloc[-1]

            entry = round(last_price, 2)
            target = round(entry * 1.015, 2)
            sl = round(entry * 0.99, 2)

            if "STRONG" not in sig:
                continue

            results.append({
                "STOCK": s,
                "PRICE": entry,
                "SIGNAL": sig,
                "SMART": sm,
                "TARGET": target,
                "STOPLOSS": sl,
                "AI SCORE": round(score,1)
            })

        if results:
            df_res = pd.DataFrame(results).sort_values(by="AI SCORE", ascending=False)
            st.dataframe(df_res, use_container_width=True)

            st.success(f"🔥 {len(df_res)} Strong Opportunities Found")

        else:
            st.warning("No strong signals found")

# =============================
# BACKTEST
# =============================
with tab2:

    bt_date = st.date_input("📅 Select Date", datetime.now(IST).date())

    if st.button("📈 RUN BACKTEST"):

        logs = []
        wins = 0
        total = 0

        for s in stocks[:30]:

            df = get_data(s, "15m")

            if df is None or len(df) < 50:
                continue

            df = add_indicators(df)
            df = df[df.index.strftime('%Y-%m-%d') == str(bt_date)]

            if len(df) < 20:
                continue

            for i in range(20, len(df)-1):

                sc = ai_score(df.iloc[:i+1])
                sig = signal(sc)

                if "STRONG" not in sig:
                    continue

                entry = df.iloc[i]['Close']
                next_price = df.iloc[i+1]['Close']

                result = "WIN" if next_price > entry else "LOSS"

                if result == "WIN":
                    wins += 1

                total += 1

                logs.append({
                    "TIME": df.index[i].strftime('%H:%M'),
                    "STOCK": s,
                    "ENTRY": round(entry,2),
                    "NEXT": round(next_price,2),
                    "RESULT": result
                })

        if logs:
            df_logs = pd.DataFrame(logs)
            acc = (wins/total)*100 if total > 0 else 0

            st.dataframe(df_logs, use_container_width=True)
            st.metric("🎯 Accuracy", f"{acc:.2f}%")

        else:
            st.warning("No trades found")

# =============================
# CHART
# =============================
st.markdown("---")
stock_sel = st.selectbox("📊 Chart View", stocks[:50])

df_chart = get_data(stock_sel, "15m")

if df_chart is not None:

    df_chart = add_indicators(df_chart)

    import plotly.graph_objects as go

    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df_chart.index,
        open=df_chart['Open'],
        high=df_chart['High'],
        low=df_chart['Low'],
        close=df_chart['Close']
    ))

    fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['EMA20'], name="EMA20"))
    fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['EMA50'], name="EMA50"))
    fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['VWAP'], name="VWAP"))

    fig.update_layout(height=600, template="plotly_dark")

    st.plotly_chart(fig, use_container_width=True)
