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
st.set_page_config(page_title="🔥 NSE AI PRO V4", layout="wide")
st_autorefresh(interval=60000, key="refresh")

st.title("🚀 NSE AI PRO TERMINAL V4 (CLEAN + TIME FIX + BIG PLAYER)")
st.markdown("---")

# =============================
# DATA LOAD
# =============================
@st.cache_data(ttl=300)
def load_data(stock):
    df = yf.Ticker(stock + ".NS").history(period="1d", interval="5m")
    return df

# =============================
# STOCKS
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
# TIME FORMAT FIX (IMPORTANT)
# =============================
def clean_time(ts):
    return pd.to_datetime(ts).strftime("%I:%M %p")

# =============================
# RSI
# =============================
def rsi(df, period=14):
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / (loss + 1e-9)
    return (100 - (100 / (1 + rs))).fillna(50)

# =============================
# AI MODEL
# =============================
def ai_predict(df):
    df = df.copy().dropna()

    if len(df) < 30:
        return None

    df['Target'] = df['Close'].shift(-1)
    df.dropna(inplace=True)

    try:
        X = df[['Close','Volume']]
        y = df['Target']

        model = LinearRegression()
        model.fit(X, y)

        return model.predict(X.iloc[-1].values.reshape(1, -1))[0]
    except:
        return None

# =============================
# BIG PLAYER DETECTION
# =============================
def big_player(df, stock):
    df = df.copy()

    df['AvgVol'] = df['Volume'].rolling(20).mean()
    df['Spike'] = df['Volume'] > (df['AvgVol'] * 2)
    df['Move'] = df['Close'].diff()

    entries = []

    for i in range(len(df)):
        if df['Spike'].iloc[i] and df['Move'].iloc[i] > 0:
            entries.append({
                "Stock": stock,
                "Type": "BIG BUY",
                "Price": df['Close'].iloc[i],
                "Time": clean_time(df.index[i])
            })

        elif df['Spike'].iloc[i] and df['Move'].iloc[i] < 0:
            entries.append({
                "Stock": stock,
                "Type": "BIG SELL",
                "Price": df['Close'].iloc[i],
                "Time": clean_time(df.index[i])
            })

    return sorted(entries, key=lambda x: x["Time"])

# =============================
# RISK
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
# ANALYSIS ENGINE
# =============================
def analyze(df):
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    df['AvgVol'] = df['Volume'].rolling(20).mean()

    r = rsi(df)
    pred = ai_predict(df)

    signal = "WAIT"

    if pred:
        signal = "BUY" if pred > df['Close'].iloc[-1] else "SELL"

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
# BREAKOUT
# =============================
def breakout(df, stock):
    try:
        opening = df.between_time("09:15","09:30")
        if len(opening) < 2:
            return []

        high = opening['High'].max()
        low = opening['Low'].min()

        for i in range(len(df)):
            if df['Close'].iloc[i] > high:
                return [{
                    "Stock": stock,
                    "Type": "BUY BO",
                    "Level": high,
                    "Time": clean_time(df.index[i])
                }]

            if df['Close'].iloc[i] < low:
                return [{
                    "Stock": stock,
                    "Type": "SELL BO",
                    "Level": low,
                    "Time": clean_time(df.index[i])
                }]
    except:
        return []

    return []

# =============================
# LIVE START
# =============================
if st.button("🔍 START LIVE V4"):

    results = []
    all_bo = []
    all_big = []

    for s in all_stocks:
        try:
            df = load_data(s)
            df = df.between_time("09:15","15:30")

            if len(df) < 50:
                continue

            res = analyze(df)
            bo = breakout(df, s)
            big = big_player(df, s)

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
            all_big += big

        except:
            pass

    st.session_state.live_res = results
    st.session_state.live_bo = all_bo
    st.session_state.big_entries = all_big

# =============================
# DISPLAY
# =============================
if "live_res" in st.session_state:

    st.subheader("📊 SIGNALS")
    st.dataframe(pd.DataFrame(st.session_state.live_res))

    st.subheader("🔥 BREAKOUT")
    st.dataframe(pd.DataFrame(st.session_state.live_bo))

    st.subheader("🐋 BIG PLAYER ENTRIES")
    st.dataframe(pd.DataFrame(st.session_state.big_entries))

    stock = st.selectbox(
        "📈 Chart",
        pd.DataFrame(st.session_state.live_res)["Stock"].unique()
    )

    df_chart = load_data(stock)
    df_chart = df_chart.between_time("09:15","15:30")

    fig = go.Figure(data=[go.Candlestick(
        x=df_chart.index,
        open=df_chart['Open'],
        high=df_chart['High'],
        low=df_chart['Low'],
        close=df_chart['Close']
    )])

    big_df = pd.DataFrame(st.session_state.big_entries)

    if not big_df.empty:
        big_df = big_df[big_df["Stock"] == stock]

        for _, row in big_df.iterrows():
            color = "green" if row["Type"] == "BIG BUY" else "red"

            fig.add_trace(go.Scatter(
                x=[df_chart.index[0]],
                y=[row["Price"]],
                mode="markers+text",
                marker=dict(size=10, color=color),
                text=[row["Type"]],
                name=row["Type"]
            ))

    st.plotly_chart(fig, use_container_width=True)
