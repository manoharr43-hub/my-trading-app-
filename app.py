import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V2", layout="wide")
st_autorefresh(interval=60000, key="refresh")

st.title("🚀 NSE AI PRO TERMINAL V2 (UPGRADED)")
st.markdown("---")

# =============================
# CACHE DATA (FAST LOADING)
# =============================
@st.cache_data(ttl=300)
def load_data(stock):
    df = yf.Ticker(stock + ".NS").history(period="1d", interval="5m")
    return df

# =============================
# STOCK LIST
# =============================
sector_map = {
    "Banking": ["HDFCBANK","ICICIBANK","SBIN","AXISBANK","KOTAKBANK"],
    "IT": ["TCS","INFY","HCLTECH","WIPRO","TECHM"],
    "Pharma": ["SUNPHARMA","DRREDDY","CIPLA"],
    "Auto": ["MARUTI","M&M","TATAMOTORS"],
    "Metals": ["JSWSTEEL","TATASTEEL","HINDALCO"],
    "FMCG": ["ITC","RELIANCE","LT","BHARTIARTL"]
}

all_stocks = list(set(sum(sector_map.values(), [])))

# =============================
# RSI (FIXED)
# =============================
def rsi(df, period=14):
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# =============================
# AI MODEL (LIGHTWEIGHT)
# =============================
def ai_predict(df):
    df = df.copy().dropna()

    if len(df) < 30:
        return None

    df['Target'] = df['Close'].shift(-1)
    df.dropna(inplace=True)

    X = df[['Close','Volume']]
    y = df['Target']

    model = LinearRegression()
    model.fit(X, y)

    return model.predict(X.iloc[-1].values.reshape(1, -1))[0]

# =============================
# RISK MANAGEMENT
# =============================
def risk(df, signal):
    price = df['Close'].iloc[-1]

    if signal == "BUY":
        sl = df['Low'].rolling(10).min().iloc[-1]
        target = price + (price - sl) * 2

    elif signal == "SELL":
        sl = df['High'].rolling(10).max().iloc[-1]
        target = price - (sl - price) * 2
    else:
        return price, None, None

    return round(price,2), round(sl,2), round(target,2)

# =============================
# ANALYSIS ENGINE (V2 IMPROVED)
# =============================
def analyze(df):
    if df is None or len(df) < 50:
        return None

    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    df['AvgVol'] = df['Volume'].rolling(20).mean()

    r = rsi(df)
    pred = ai_predict(df)

    signal = "WAIT"

    if pred:
        if pred > df['Close'].iloc[-1]:
            signal = "BUY"
        else:
            signal = "SELL"

    entry, sl, tgt = risk(df, signal)

    vol_ok = df['Volume'].iloc[-1] > df['AvgVol'].iloc[-1]

    trend_up = df['EMA20'].iloc[-1] > df['EMA50'].iloc[-1]
    trend_down = df['EMA20'].iloc[-1] < df['EMA50'].iloc[-1]

    final = "⚠️ WAIT"

    if signal == "BUY" and r.iloc[-1] < 70 and vol_ok and trend_up:
        final = "🚀 STRONG BUY"

    elif signal == "SELL" and r.iloc[-1] > 30 and vol_ok and trend_down:
        final = "💀 STRONG SELL"

    return signal, round(r.iloc[-1],2), entry, sl, tgt, final

# =============================
# BREAKOUT (IMPROVED)
# =============================
def breakout(df, stock):
    res = []

    opening = df.between_time("09:15","09:30")
    if len(opening) < 2:
        return res

    high = opening['High'].max()
    low = opening['Low'].min()

    for i in range(len(df)):
        if df['Close'].iloc[i] > high:
            res.append({
                "Stock": stock,
                "Type": "BUY BO",
                "Level": high,
                "Time": df.index[i].strftime("%H:%M"),
                "DateTime": df.index[i]
            })
            break

        if df['Close'].iloc[i] < low:
            res.append({
                "Stock": stock,
                "Type": "SELL BO",
                "Level": low,
                "Time": df.index[i].strftime("%H:%M"),
                "DateTime": df.index[i]
            })
            break

    return res

# =============================
# LIVE RUN
# =============================
if st.button("🔍 START LIVE V2"):
    results = []
    all_bo = []

    for s in all_stocks:
        try:
            df = load_data(s)
            df = df.between_time("09:15","15:30")

            if len(df) < 50:
                continue

            res = analyze(df)
            bo = breakout(df, s)

            if res:
                signal, rsi_v, entry, sl, tgt, final = res

                results.append({
                    "Stock": s,
                    "Signal": signal,
                    "FINAL": final,
                    "Entry": entry,
                    "SL": sl,
                    "Target": tgt,
                    "RSI": rsi_v
                })

            all_bo += bo

        except:
            pass

    st.session_state.live_res = results
    st.session_state.live_bo = all_bo

# =============================
# DISPLAY LIVE
# =============================
if "live_res" in st.session_state and st.session_state.live_res:
    df_res = pd.DataFrame(st.session_state.live_res)
    df_bo = pd.DataFrame(st.session_state.live_bo)

    st.subheader("📊 LIVE SIGNALS V2")
    st.dataframe(df_res, use_container_width=True)

    st.subheader("🔥 BREAKOUT")
    if not df_bo.empty:
        st.dataframe(df_bo.drop(columns=["DateTime"]), use_container_width=True)

    stock = st.selectbox("📈 Chart", df_res["Stock"].unique())
    df_chart = load_data(stock)
    df_chart = df_chart.between_time("09:15","15:30")

    fig = go.Figure(data=[go.Candlestick(
        x=df_chart.index,
        open=df_chart['Open'],
        high=df_chart['High'],
        low=df_chart['Low'],
        close=df_chart['Close']
    )])

    st.plotly_chart(fig, use_container_width=True)

# =============================
# BACKTEST V2
# =============================
bt_date = st.sidebar.date_input("📅 Backtest Date", datetime.now().date() - timedelta(days=1))

if st.button("📊 BACKTEST V2"):
    bt_res = []
    bt_bo = []

    for s in all_stocks:
        try:
            df = yf.Ticker(s + ".NS").history(
                start=bt_date,
                end=bt_date + timedelta(days=1),
                interval="5m"
            )

            df = df.between_time("09:15","15:30")

            if len(df) < 50:
                continue

            res = analyze(df)
            bo = breakout(df, s)

            if res:
                signal, rsi_v, entry, sl, tgt, final = res

                bt_res.append({
                    "Stock": s,
                    "Signal": signal,
                    "FINAL": final,
                    "Entry": entry,
                    "SL": sl,
                    "Target": tgt
                })

            bt_bo += bo

        except:
            pass

    st.session_state.bt_res = bt_res
    st.session_state.bt_bo = bt_bo

# =============================
# BACKTEST DISPLAY SAFE
# =============================
if "bt_res" in st.session_state and st.session_state.bt_res:
    df_bt = pd.DataFrame(st.session_state.bt_res)

    st.subheader("📊 BACKTEST V2")
    st.dataframe(df_bt, use_container_width=True)

    if not df_bt.empty:
        stock = st.selectbox("📉 Backtest Chart", df_bt["Stock"].unique())
