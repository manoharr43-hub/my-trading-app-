import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V8", layout="wide")
st.title("🚀 NSE AI PRO V8 (AUTO TIME SCAN + BIG PLAYER)")
st.markdown("---")

# =============================
# STOCK LIST (FAST SCAN)
# =============================
stocks = [
    "RELIANCE","HDFCBANK","ICICIBANK","SBIN","AXISBANK",
    "TCS","INFY","WIPRO","HCLTECH",
    "ITC","LT","BHARTIARTL","MARUTI","TATAMOTORS"
]

# =============================
# TIME FORMAT
# =============================
def clean_time(ts):
    return pd.to_datetime(ts).strftime("%I:%M %p").lstrip("0")

# =============================
# DYNAMIC MARKET TIME
# =============================
def get_market_end_time():
    now = datetime.now()
    current = now.strftime("%H:%M")

    if current > "15:30":
        return "15:30"
    elif current < "09:15":
        return "09:15"
    else:
        return current

# =============================
# DATA LOAD
# =============================
def load_data(stock):
    return yf.Ticker(stock + ".NS").history(period="1d", interval="5m")

# =============================
# BIG PLAYER DETECTION
# =============================
def big_player(df, stock):
    df = df.copy()

    df['AvgVol'] = df['Volume'].rolling(20).mean()
    df['Spike'] = df['Volume'] > df['AvgVol'] * 2
    df['Move'] = df['Close'].diff()

    entries = []

    for i in range(len(df)):
        if df['Spike'].iloc[i] and df['Move'].iloc[i] > 0:
            entries.append({
                "Stock": stock,
                "Type": "BIG BUY",
                "Price": df['Close'].iloc[i],
                "TimeRaw": df.index[i],
                "Time": clean_time(df.index[i])
            })

        elif df['Spike'].iloc[i] and df['Move'].iloc[i] < 0:
            entries.append({
                "Stock": stock,
                "Type": "BIG SELL",
                "Price": df['Close'].iloc[i],
                "TimeRaw": df.index[i],
                "Time": clean_time(df.index[i])
            })

    # SERIAL ORDER
    return sorted(entries, key=lambda x: x["TimeRaw"])

# =============================
# LIVE SCAN
# =============================
if st.button("🔍 START AUTO SCAN"):

    end_time = get_market_end_time()
    all_big = []

    for s in stocks:
        try:
            df = load_data(s)

            if df.empty:
                continue

            # 🔥 AUTO TIME FILTER
            df = df.between_time("09:15", end_time)

            if len(df) < 30:
                continue

            big = big_player(df, s)
            all_big += big

        except:
            continue

    st.session_state.big_data = sorted(all_big, key=lambda x: x["TimeRaw"])
    st.session_state.scan_time = end_time

# =============================
# DISPLAY
# =============================
if "big_data" in st.session_state:

    st.info(f"📊 Scan Time: 09:15 AM → {st.session_state.scan_time}")

    df = pd.DataFrame(st.session_state.big_data)

    st.subheader("🐋 BIG PLAYER REPORT")
    st.dataframe(df[["Stock","Type","Price","Time"]])

    # =============================
    # CHART
    # =============================
    stock = st.selectbox("📈 Select Stock", stocks)

    df_chart = load_data(stock)
    df_chart = df_chart.between_time("09:15", st.session_state.scan_time)

    fig = go.Figure(data=[go.Candlestick(
        x=df_chart.index,
        open=df_chart['Open'],
        high=df_chart['High'],
        low=df_chart['Low'],
        close=df_chart['Close']
    )])

    df_stock = df[df["Stock"] == stock]

    for _, row in df_stock.iterrows():
        fig.add_trace(go.Scatter(
            x=[row["TimeRaw"]],
            y=[row["Price"]],
            mode="markers+text",
            marker=dict(size=12, color="green" if row["Type"]=="BIG BUY" else "red"),
            text=[row["Type"]],
            textposition="top center"
        ))

    st.plotly_chart(fig, use_container_width=True)
