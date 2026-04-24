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
st.set_page_config(page_title="🔥 NSE AI PRO TERMINAL", layout="wide")
st_autorefresh(interval=60000, key="refresh")

st.title("🚀 NSE AI PRO TERMINAL (FINAL ALL FIXED)")
st.markdown("---")

# =============================
# SESSION STATE
# =============================
for key in ["live_res","live_bo","bt_res","bt_bo"]:
    if key not in st.session_state:
        st.session_state[key] = []

# =============================
# SECTOR MAP
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
selected_sector = st.sidebar.selectbox("📂 Sector", list(sector_map.keys()))
stocks = sector_map[selected_sector]

# =============================
# INDICATORS
# =============================
def calculate_rsi(df, period=14):
    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def ai_prediction(df):
    df = df.copy()
    df['Target'] = df['Close'].shift(-1)
    df.dropna(inplace=True)
    if len(df) < 10:
        return None
    X = np.array(df[['Close','Volume']])
    y = np.array(df['Target'])
    model = LinearRegression()
    model.fit(X, y)
    return model.predict(X[-1].reshape(1, -1))[0]

# =============================
# RISK MANAGEMENT
# =============================
def risk_management(df, signal):
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
# ANALYSIS
# =============================
def analyze_data(df):
    if df is None or len(df) < 50:
        return None
    rsi = calculate_rsi(df)
    pred = ai_prediction(df)
    signal = "WAIT"
    if pred:
        if pred > df['Close'].iloc[-1]:
            signal = "BUY"
        elif pred < df['Close'].iloc[-1]:
            signal = "SELL"
    entry, sl, tgt = risk_management(df, signal)
    return signal, round(rsi.iloc[-1],2), entry, sl, tgt

# =============================
# BREAKOUT ENGINE
# =============================
def breakout_engine(df, stock):
    results = []
    opening = df.between_time("09:15","09:30")
    if opening.empty:
        return results
    high = opening['High'].max()
    low = opening['Low'].min()
    for i in range(1, len(df)):
        dt = df.index[i]
        if df['Close'].iloc[i] > high:
            results.append({"Stock": stock,"Type": "BUY BO","Level": high,"Time": dt.strftime("%H:%M"),"DateTime": dt})
            break
        elif df['Close'].iloc[i] < low:
            results.append({"Stock": stock,"Type": "SELL BO","Level": low,"Time": dt.strftime("%H:%M"),"DateTime": dt})
            break
    return results

# =============================
# CHART
# =============================
def plot_chart(df, stock, bo):
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df.index,open=df['Open'],high=df['High'],low=df['Low'],close=df['Close']))
    fig.add_trace(go.Bar(x=df.index,y=df['Volume'],yaxis="y2",opacity=0.3))
    if bo:
        for b in bo:
            color = "green" if "BUY" in b["Type"] else "red"
            fig.add_trace(go.Scatter(x=[b["DateTime"]],y=[b["Level"]],mode="markers+text",
                                     marker=dict(color=color, size=12),text=[b["Type"]],textposition="top center"))
    fig.update_layout(yaxis2=dict(overlaying='y', side='right'), height=600)
    st.plotly_chart(fig, use_container_width=True)

# =============================
# LIVE SCANNER
# =============================
if st.button("🔍 START LIVE"):
    results, all_bo = [], []
    for s in all_stocks:
        try:
            df = yf.Ticker(s + ".NS").history(period="1d", interval="5m")
            df = df.between_time("09:15","15:30")
            if len(df) < 50: continue
            res = analyze_data(df)
            bo = breakout_engine(df, s)
            if res:
                signal, rsi, entry, sl, tgt = res
                results.append({"Stock": s,"Signal": signal,"Entry": entry,"SL": sl,"Target": tgt,"RSI": rsi})
            all_bo += bo
        except Exception as e:
            st.warning(f"{s} error: {e}")
    st.session_state.live_res, st.session_state.live_bo = results, all_bo

# =============================
# LIVE DISPLAY
# =============================
if st.session_state.live_res:
    df_res = pd.DataFrame(st.session_state.live_res)
    df_bo = pd.DataFrame(st.session_state.live_bo)
    if not df_bo.empty: df_bo = df_bo.sort_values(by="DateTime")
    st.subheader("📊 LIVE SIGNALS"); st.dataframe(df_res, use_container_width=True)
    st.subheader("🔥 LIVE BREAKOUT"); st.dataframe(df_bo.drop(columns=["DateTime"]), use_container_width=True)
    live_stock = st.selectbox("📈 Select Live Stock", df_res["Stock"].unique())
    if live_stock:
        df_chart = yf.Ticker(live_stock + ".NS").history(period="1d", interval="5m")
        df_chart = df_chart.between_time("09:15","15:30")
        bo_chart = breakout_engine(df_chart, live_stock)
        plot_chart(df_chart, live_stock, bo_chart)

# =============================
# BACKTEST
# =============================
bt_date = st.sidebar.date_input("📅 Backtest Date", datetime.now().date() - timedelta(days=1))
if st.button("📊 RUN BACKTEST"):
    bt_res, bt_bo = [], []
    for s in all_stocks:
        try:
            df = yf.Ticker(s + ".NS").history(start=bt_date,end=bt_date + timedelta(days=1),interval="5m")
            df = df.between_time("09:15","15:30")
            if len(df) < 50: continue
            res = analyze_data(df)
            bo = breakout_engine(df, s)
            if res:
                signal, rsi, entry, sl, tgt = res
                bt_res.append({"Stock": s,"Signal": signal,"Entry": entry,"SL": sl,"Target": tgt,"Time": df.index[-1].strftime("%H:%M")})
            bt_bo += bo
        except Exception as e:
            st.warning(f"{s} error: {e}")
    st.session_state.bt_res, st.session_state.bt_bo = bt_res, bt_bo

# =============================
# BACKTEST DISPLAY
# =============================
if st.session_state.bt_res:
    df_bt = pd.DataFrame(st.session_state.bt_res)
    df_bo = pd.DataFrame(st.session_state.bt_bo)
    st.subheader("📊 BACKTEST RESULTS"); st.dataframe(df_bt, use_container_width=True)
    st.subheader("🔥 BACKTEST BREAKOUT"); st.dataframe(df_bo.drop(columns=["DateTime"]), use_container_width=True)
    bt_stock = st.selectbox("📉 Select Backtest Stock
