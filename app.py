import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V9", layout="wide")
st.title("🚀 NSE AI PRO V9 (NO EMPTY + SMART SCANNER)")
st.markdown("---")

# =============================
# STOCK LIST
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
# MARKET TIME
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
# BIG PLAYER LOGIC (IMPROVED)
# =============================
def big_player(df, stock):
    df = df.copy()

    df['AvgVol'] = df['Volume'].rolling(20).mean()
    df['Spike'] = df['Volume'] > df['AvgVol'] * 1.8   # 🔥 improved sensitivity
    df['Move'] = df['Close'].diff()

    entries = []

    for i in range(len(df)):
        if df['Spike'].iloc[i]:
            entries.append({
                "Stock": stock,
                "Type": "BIG BUY" if df['Move'].iloc[i] > 0 else "BIG SELL",
                "Price": df['Close'].iloc[i],
                "TimeRaw": df.index[i],
                "Time": clean_time(df.index[i])
            })

    return sorted(entries, key=lambda x: x["TimeRaw"])

# =============================
# FALLBACK: ACTIVE STOCKS
# =============================
def get_active_stocks(df, stock):
    change = ((df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0]) * 100
    vol = df['Volume'].sum()

    return {
        "Stock": stock,
        "Change %": round(change,2),
        "Volume": int(vol)
    }

# =============================
# SCAN
# =============================
if st.button("🔍 START SMART SCAN"):

    end_time = get_market_end_time()

    all_big = []
    active_list = []

    for s in stocks:
        try:
            df = load_data(s)

            if df.empty:
                continue

            df = df.between_time("09:15", end_time)

            if len(df) < 30:
                continue

            # Big player
            big = big_player(df, s)
            all_big += big

            # Active fallback
            active_list.append(get_active_stocks(df, s))

        except:
            continue

    st.session_state.big_data = sorted(all_big, key=lambda x: x["TimeRaw"])
    st.session_state.active = pd.DataFrame(active_list).sort_values(by="Volume", ascending=False)
    st.session_state.scan_time = end_time

# =============================
# DISPLAY
# =============================
if "scan_time" in st.session_state:

    st.info(f"📊 Scan Time: 09:15 AM → {st.session_state.scan_time}")

    df_big = pd.DataFrame(st.session_state.big_data)

    # =============================
    # BIG PLAYER DISPLAY
    # =============================
    st.subheader("🐋 BIG PLAYER SIGNALS")

    if not df_big.empty:
        st.dataframe(df_big[["Stock","Type","Price","Time"]])
    else:
        st.warning("⚠️ No Big Player signals — Showing Active Stocks")

    # =============================
    # FALLBACK DISPLAY
    # =============================
    st.subheader("🔥 ACTIVE STOCKS (Fallback)")

    if not st.session_state.active.empty:
        st.dataframe(st.session_state.active.head(10))

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

    # Big Player markers
    if not df_big.empty:
        df_stock = df_big[df_big["Stock"] == stock]

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
