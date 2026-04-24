import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO TERMINAL", layout="wide")

st.title("🚀 NSE AI PRO TERMINAL (ULTIMATE FIXED)")
st.markdown("---")

# =============================
# NSE SECTORS
# =============================
sector_map = {
    "Banking": ["HDFCBANK","ICICIBANK","SBIN","AXISBANK","KOTAKBANK"],
    "IT": ["TCS","INFY","HCLTECH","WIPRO","TECHM"],
    "Pharma": ["SUNPHARMA","DRREDDY","CIPLA","LUPIN"],
    "Auto": ["MARUTI","TATAMOTORS","M&M"],
    "FMCG": ["ITC","HINDUNILVR","NESTLEIND"],
    "Energy": ["RELIANCE","ONGC","IOC"],
    "All NSE (Top)": ["RELIANCE","HDFCBANK","ICICIBANK","INFY","TCS","SBIN","ITC","LT"]
}

selected_sector = st.sidebar.selectbox("📂 Select Sector", list(sector_map.keys()))
stocks = sector_map[selected_sector]

# =============================
# INDICATORS
# =============================
def rsi(df):
    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    rs = gain.rolling(14).mean() / loss.rolling(14).mean()
    return 100 - (100/(1+rs))

def macd(df):
    e12 = df['Close'].ewm(span=12).mean()
    e26 = df['Close'].ewm(span=26).mean()
    macd = e12 - e26
    signal = macd.ewm(span=9).mean()
    return macd, signal

# =============================
# STRATEGY
# =============================
def strategy(df):
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    macd_val, sig = macd(df)
    r = rsi(df)

    opening = df.between_time("09:15","09:30")
    if opening.empty:
        return None

    high = opening['High'].max()
    low = opening['Low'].min()

    last = df.iloc[-1]
    prev = df.iloc[-2]

    if (
        last['Close'] > high and prev['Close'] <= high and
        df['EMA20'].iloc[-1] > df['EMA50'].iloc[-1] and
        macd_val.iloc[-1] > sig.iloc[-1] and
        40 < r.iloc[-1] < 65
    ):
        return "BUY", high, low

    elif (
        last['Close'] < low and prev['Close'] >= low and
        df['EMA20'].iloc[-1] < df['EMA50'].iloc[-1] and
        macd_val.iloc[-1] < sig.iloc[-1] and
        35 < r.iloc[-1] < 60
    ):
        return "SELL", high, low

    return None

# =============================
# STRENGTH
# =============================
def strength(df):
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    return "STRONG" if df['EMA20'].iloc[-1] > df['EMA50'].iloc[-1] else "WEAK"

# =============================
# CHART
# =============================
def plot_chart(df, stock, high=None, low=None, signal=None):
    fig = go.Figure()

    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close']
    ))

    fig.add_trace(go.Scatter(x=df.index, y=df['EMA20'], name="EMA20"))
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA50'], name="EMA50"))

    if high:
        fig.add_hline(y=high, line_dash="dash")
    if low:
        fig.add_hline(y=low, line_dash="dash")

    if signal:
        fig.add_trace(go.Scatter(
            x=[df.index[-1]],
            y=[df['Close'].iloc[-1]],
            mode="markers+text",
            text=[signal],
            marker=dict(size=12)
        ))

    fig.update_layout(title=stock, xaxis_rangeslider_visible=False, height=400)
    st.plotly_chart(fig, use_container_width=True)

# =============================
# LIVE SCANNER
# =============================
if st.button("🔍 START LIVE SCANNER"):
    results = []

    for s in stocks:
        try:
            df = yf.Ticker(s + ".NS").history(period="5d", interval="5m")
            df = df.between_time("09:15","15:30")

            if df.empty:
                continue

            res = strategy(df)

            opening = df.between_time("09:15","09:30")
            high = opening['High'].max() if not opening.empty else None
            low = opening['Low'].min() if not opening.empty else None

            signal = None

            if res:
                signal, high, low = res
                entry = df['Close'].iloc[-1]
                sl = low if signal == "BUY" else high

                results.append({
                    "Stock": s,
                    "Signal": signal,
                    "Entry": round(entry,2),
                    "SL": round(sl,2),
                    "Time": df.index[-1].strftime("%H:%M")
                })

            # ✅ Clean chart UI
            with st.expander(f"📊 {s} Chart"):
                plot_chart(df, s, high, low, signal)

        except:
            continue

    if results:
        st.subheader("📊 LIVE SIGNALS")
        st.dataframe(pd.DataFrame(results), use_container_width=True)
    else:
        st.warning("No Signals Found")

# =============================
# STRONG vs WEAK
# =============================
st.markdown("---")
if st.button("💪 CHECK MARKET STRENGTH"):
    strong, weak = [], []

    for s in stocks:
        try:
            df = yf.Ticker(s + ".NS").history(period="1d", interval="5m")
            if df.empty:
                continue

            if strength(df) == "STRONG":
                strong.append(s)
            else:
                weak.append(s)

        except:
            continue

    col1, col2 = st.columns(2)

    with col1:
        st.success("🔥 STRONG STOCKS")
        st.write(strong)

    with col2:
        st.error("💀 WEAK STOCKS")
        st.write(weak)

# =============================
# ALL SIGNALS
# =============================
st.markdown("---")
if st.button("⚡ ALL STOCK SIGNALS"):
    all_res = []

    for s in stocks:
        try:
            df = yf.Ticker(s + ".NS").history(period="1d", interval="5m")
            df = df.between_time("09:15","15:30")

            if df.empty:
                continue

            res = strategy(df)

            if res:
                signal, high, low = res
                all_res.append({
                    "Time": df.index[-1].strftime("%H:%M"),
                    "Stock": s,
                    "Signal": signal
                })

        except:
            continue

    st.dataframe(pd.DataFrame(all_res), use_container_width=True)

# =============================
# BACKTEST
# =============================
st.markdown("---")
bt_date = st.sidebar.date_input("📅 Backtest Date", datetime.now().date() - timedelta(days=1))

if st.button("📊 RUN BACKTEST"):
    bt_results = []

    for s in stocks:
        try:
            df = yf.Ticker(s + ".NS").history(
                start=pd.to_datetime(bt_date),
                end=pd.to_datetime(bt_date)+timedelta(days=1),
                interval="5m"
            )

            df = df.between_time("09:15","15:30")

            if df.empty:
                continue

            res = strategy(df)

            if res:
                signal, high, low = res
                bt_results.append({
                    "Stock": s,
                    "Signal": signal
                })

            with st.expander(f"📊 {s} Backtest Chart"):
                plot_chart(df, s, high, low, signal if res else None)

        except:
            continue

    if bt_results:
        st.dataframe(pd.DataFrame(bt_results), use_container_width=True)
    else:
        st.warning("No Backtest Signals")
