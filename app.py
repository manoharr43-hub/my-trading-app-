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

st.title("🚀 NSE AI PRO TERMINAL (CLEAN VERSION)")
st.markdown("---")

# =============================
# SESSION STATE
# =============================
for key in ["live_res","live_bo","bt_res","bt_bo"]:
    if key not in st.session_state:
        st.session_state[key] = []

# =============================
# STOCK LIST
# =============================
stocks = [
    "HDFCBANK","ICICIBANK","SBIN","AXISBANK","KOTAKBANK",
    "TCS","INFY","HCLTECH","WIPRO","TECHM",
    "SUNPHARMA","DRREDDY","CIPLA",
    "MARUTI","M&M","TATAMOTORS",
    "JSWSTEEL","TATASTEEL","HINDALCO",
    "ITC","RELIANCE","LT","BHARTIARTL"
]

# =============================
# DATA FETCH
# =============================
def fetch_data(symbol, start=None, end=None):
    try:
        if start:
            df = yf.Ticker(symbol + ".NS").history(
                start=start,
                end=end,
                interval="5m"
            )
        else:
            df = yf.Ticker(symbol + ".NS").history(
                period="1d",
                interval="5m"
            )

        if df.empty:
            return None

        df = df.between_time("09:15","15:30")
        df.dropna(inplace=True)

        return df

    except:
        return None

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
    df['Returns'] = df['Close'].pct_change()
    df['Volatility'] = df['Returns'].rolling(5).std()
    df.dropna(inplace=True)

    if len(df) < 20:
        return None

    X = df[['Close','Volume','Returns','Volatility']]
    y = df['Target']

    model = LinearRegression()
    model.fit(X, y)

    return model.predict(X.iloc[[-1]])[0]

# =============================
# RISK
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

    df['AvgVol'] = df['Volume'].rolling(20).mean()
    df['EMA20'] = df['Close'].ewm(span=20).mean()

    rsi = calculate_rsi(df)
    pred = ai_prediction(df)

    if pred is None:
        return None

    price = df['Close'].iloc[-1]

    if pred > price * 1.002:
        signal = "BUY"
    elif pred < price * 0.998:
        signal = "SELL"
    else:
        signal = "WAIT"

    if signal == "BUY" and price < df['EMA20'].iloc[-1]:
        signal = "WAIT"
    if signal == "SELL" and price > df['EMA20'].iloc[-1]:
        signal = "WAIT"

    entry, sl, tgt = risk_management(df, signal)

    vol_ok = df['Volume'].iloc[-1] > df['AvgVol'].iloc[-1]

    final = "⚠️ WAIT"
    if signal == "BUY" and rsi.iloc[-1] < 60 and vol_ok:
        final = "🚀 STRONG BUY"
    elif signal == "SELL" and rsi.iloc[-1] > 40 and vol_ok:
        final = "💀 STRONG SELL"

    return signal, round(rsi.iloc[-1],2), entry, sl, tgt, final

# =============================
# BREAKOUT
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
            results.append({
                "Stock": stock,
                "Type": "BUY BO",
                "Level": round(high,2),
                "Time": dt.strftime("%H:%M"),
                "DateTime": dt
            })
            break

        elif df['Close'].iloc[i] < low:
            results.append({
                "Stock": stock,
                "Type": "SELL BO",
                "Level": round(low,2),
                "Time": dt.strftime("%H:%M"),
                "DateTime": dt
            })
            break

    return results

# =============================
# CHART
# =============================
def plot_chart(df, stock, bo):
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close']
    ))

    fig.add_trace(go.Bar(
        x=df.index,
        y=df['Volume'],
        yaxis="y2",
        opacity=0.3
    ))

    if bo:
        for b in bo:
            color = "green" if "BUY" in b["Type"] else "red"
            fig.add_trace(go.Scatter(
                x=[b["DateTime"]],
                y=[b["Level"]],
                mode="markers+text",
                marker=dict(color=color, size=12),
                text=[b["Type"]],
                textposition="top center"
            ))

    fig.update_layout(yaxis2=dict(overlaying='y', side='right'), height=600)
    st.plotly_chart(fig, use_container_width=True)

# =============================
# LIVE
# =============================
if st.button("🔍 START LIVE"):
    results = []
    all_bo = []

    for s in stocks:
        df = fetch_data(s)

        if df is None or len(df) < 50:
            continue

        res = analyze_data(df)
        bo = breakout_engine(df, s)

        if res:
            signal, rsi, entry, sl, tgt, final = res

            results.append({
                "Stock": s,
                "Signal": signal,
                "FINAL": final,
                "Entry": entry,
                "SL": sl,
                "Target": tgt,
                "RSI": rsi
            })

        all_bo += bo

    st.session_state.live_res = results
    st.session_state.live_bo = all_bo

if st.session_state.live_res:
    df_res = pd.DataFrame(st.session_state.live_res)

    priority = {"🚀 STRONG BUY":1, "💀 STRONG SELL":2, "⚠️ WAIT":3}
    df_res["Rank"] = df_res["FINAL"].map(priority)

    df_res = df_res.sort_values(by=["Rank","RSI"])

    st.subheader("📊 LIVE SIGNALS")
    st.dataframe(df_res.drop(columns=["Rank"]), use_container_width=True)

    st.subheader("🔥 TOP TRADES")
    st.dataframe(df_res[df_res["FINAL"]!="⚠️ WAIT"].head(5), use_container_width=True)

    df_bo = pd.DataFrame(st.session_state.live_bo)
    if not df_bo.empty:
        st.subheader("🔥 LIVE BREAKOUT")
        st.dataframe(df_bo.drop(columns=["DateTime"]), use_container_width=True)

    stock = st.selectbox("📈 Live Chart", df_res["Stock"].unique())
    df_chart = fetch_data(stock)
    plot_chart(df_chart, stock, breakout_engine(df_chart, stock))

# =============================
# BACKTEST
# =============================
bt_date = st.sidebar.date_input("📅 Backtest Date", datetime.now().date() - timedelta(days=1))

if st.button("📊 RUN BACKTEST"):
    bt_res = []
    bt_bo = []

    for s in stocks:
        df = fetch_data(s, start=bt_date, end=bt_date + timedelta(days=1))

        if df is None or len(df) < 50:
            continue

        res = analyze_data(df)
        bo = breakout_engine(df, s)

        if res:
            signal, rsi, entry, sl, tgt, final = res

            bt_res.append({
                "Stock": s,
                "Signal": signal,
                "FINAL": final,
                "Entry": entry,
                "SL": sl,
                "Target": tgt,
                "Time": df.index[-1].strftime("%H:%M")
            })

        bt_bo += bo

    st.session_state.bt_res = bt_res
    st.session_state.bt_bo = bt_bo

if st.session_state.bt_res:
    df_bt = pd.DataFrame(st.session_state.bt_res)

    st.subheader("📊 BACKTEST RESULTS")
    st.dataframe(df_bt, use_container_width=True)

    df_bo = pd.DataFrame(st.session_state.bt_bo)
    if not df_bo.empty:
        st.subheader("🔥 BACKTEST BREAKOUT")
        st.dataframe(df_bo.drop(columns=["DateTime"]), use_container_width=True)

    stock = st.selectbox("📉 Backtest Chart", df_bt["Stock"].unique())
    df_chart = fetch_data(stock, start=bt_date, end=bt_date + timedelta(days=1))
    plot_chart(df_chart, stock, breakout_engine(df_chart, stock))
