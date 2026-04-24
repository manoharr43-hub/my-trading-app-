import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh
import plotly.graph_objects as go

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO TERMINAL", layout="wide")
st_autorefresh(interval=60000, key="refresh")

st.title("🚀 NSE AI PRO TERMINAL (Intraday Special)")
st.markdown("---")

# =============================
# STOCK LIST + SECTORS
# =============================
sectors = {
    "Banking": ["HDFCBANK","ICICIBANK","SBIN","AXISBANK","KOTAKBANK"],
    "IT": ["TCS","INFY","HCLTECH","WIPRO","TECHM"],
    "Pharma": ["SUNPHARMA","DRREDDY","CIPLA"],
    "Metals": ["JSWSTEEL","TATASTEEL","HINDALCO"],
    "Others": ["RELIANCE","ITC","LT","BHARTIARTL","MARUTI","M&M","TATAMOTORS"]
}

sector_choice = st.sidebar.selectbox("📂 Select Sector", list(sectors.keys()))
stocks = sectors[sector_choice]

# =============================
# ANALYSIS ENGINE
# =============================
def analyze_data(df):
    if df is None or len(df) < 20:
        return None

    e20 = df['Close'].ewm(span=20).mean()
    e50 = df['Close'].ewm(span=50).mean()

    vol = df['Volume']
    avg_vol = vol.rolling(20).mean()

    if pd.isna(avg_vol.iloc[-1]):
        return None

    trend = "CALL STRONG" if e20.iloc[-1] > e50.iloc[-1] else "PUT STRONG"

    signal = "WAIT"
    if e20.iloc[-1] > e50.iloc[-1] and vol.iloc[-1] > avg_vol.iloc[-1]:
        signal = "🚀 STRONG BUY"
    elif e20.iloc[-1] < e50.iloc[-1] and vol.iloc[-1] > avg_vol.iloc[-1]:
        signal = "💀 STRONG SELL"

    return trend, signal

# =============================
# BREAKOUT ENGINE
# =============================
def breakout_engine(df, stock):
    results = []
    opening = df.between_time("09:15", "09:30")
    if opening.empty:
        return results

    high = opening['High'].max()
    low = opening['Low'].min()

    for i in range(1, len(df)-3):
        prev = df.iloc[i-1]
        curr = df.iloc[i]
        t = df.index[i]

        if prev['Close'] <= high and curr['Close'] > high:
            future = df.iloc[i+1:i+4]
            up = sum(future['Close'] > curr['Close'])
            down = sum(future['Close'] <= curr['Close'])
            status = "🚀 CONFIRMED BUY" if up > down else "⚠️ FAILED BUY → SELL"
            results.append({"Time": t,"Stock": stock,"Type": status,"Level": round(high,2)})
            break

        elif prev['Close'] >= low and curr['Close'] < low:
            future = df.iloc[i+1:i+4]
            down = sum(future['Close'] < curr['Close'])
            up = sum(future['Close'] >= curr['Close'])
            status = "💀 CONFIRMED SELL" if down > up else "⚠️ FAILED SELL → BUY"
            results.append({"Time": t,"Stock": stock,"Type": status,"Level": round(low,2)})
            break

    return results

# =============================
# DASHBOARD TABS
# =============================
tab1, tab2, tab3 = st.tabs(["📊 Live Scanner","📅 Backtest","📈 Charts"])

# =============================
# TAB 1: LIVE SCANNER
# =============================
with tab1:
    if st.button("🔍 START LIVE SCANNER (9:15–3:30)"):
        live_results = []
        breakout_results = []

        for s in stocks:
            try:
                df = yf.Ticker(s + ".NS").history(period="1d", interval="5m")
                if df.empty: continue
                df = df.between_time("09:15","15:30")

                res = analyze_data(df)
                if res:
                    live_results.append({
                        "Stock": s,
                        "Price": df['Close'].iloc[-1],
                        "Trend": res[0],
                        "Signal": res[1],
                        "Time": df.index[-1].strftime("%H:%M")
                    })
                    # Alerts
                    if res[1] == "🚀 STRONG BUY":
                        st.success(f"{s}: STRONG BUY at {df['Close'].iloc[-1]}")
                    elif res[1] == "💀 STRONG SELL":
                        st.error(f"{s}: STRONG SELL at {df['Close'].iloc[-1]}")

                breakout_results += breakout_engine(df, s)

            except: continue

        breakout_results = sorted(breakout_results, key=lambda x: x["Time"])
        for x in breakout_results:
            x["Time"] = pd.to_datetime(x["Time"]).strftime("%H:%M")

        st.subheader("📊 LIVE SIGNALS")
        st.dataframe(pd.DataFrame(live_results), use_container_width=True)

        st.subheader("🔥 SMART BREAKOUT")
        st.dataframe(pd.DataFrame(breakout_results), use_container_width=True)

# =============================
# TAB 2: BACKTEST
# =============================
with tab2:
    bt_start = st.sidebar.date_input("📅 Backtest Start Date", datetime.now()-timedelta(days=5))
    bt_end = st.sidebar.date_input("📅 Backtest End Date", datetime.now()-timedelta(days=1))

    if st.button("📊 RUN BACKTEST"):
        bt_signals, bt_breakout = [], []
        for s in stocks:
            try:
                df = yf.Ticker(s + ".NS").history(start=bt_start, end=bt_end+timedelta(days=1), interval="15m")
                df = df.between_time("09:15","15:30")
                if df.empty: continue

                for i in range(20,len(df)):
                    sub = df.iloc[:i+1]
                    res = analyze_data(sub)
                    if res and res[1]!="WAIT":
                        bt_signals.append({"Time": sub.index[-1],"Stock": s,"Signal": res[1]})

                bt_breakout += breakout_engine(df,s)

            except: continue

        bt_signals = sorted(bt_signals,key=lambda x:x["Time"])
        bt_breakout = sorted(bt_breakout,key=lambda x:x["Time"])
        for x in bt_signals: x["Time"]=pd.to_datetime(x["Time"]).strftime("%H:%M")
        for x in bt_breakout: x["Time"]=pd.to_datetime(x["Time"]).strftime("%H:%M")

        st.subheader("📊 BACKTEST SIGNALS")
        st.dataframe(pd.DataFrame(bt_signals),use_container_width=True)

        st.subheader("🔥 BACKTEST BREAKOUTS")
        st.dataframe(pd.DataFrame(bt_breakout),use_container_width=True)

# =============================
# TAB 3: CHARTS
# =============================
with tab3:
    stock_choice = st.selectbox("📈 Select Stock for Chart", stocks)
    df = yf.Ticker(stock_choice + ".NS").history(period="1d", interval="5m")
    df = df.between_time("09:15","15:30")

    fig = go.Figure(data=[go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close']
    )])
    fig.update_layout(title=f"{stock_choice} Intraday Chart", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
