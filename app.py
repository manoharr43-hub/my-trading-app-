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

st.title("🚀 NSE AI PRO TERMINAL (AI UPGRADED)")
st.markdown("---")

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

selected_sector = st.sidebar.selectbox("📂 Select Sector", list(sector_map.keys()))
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

def calculate_macd(df):
    ema12 = df['Close'].ewm(span=12).mean()
    ema26 = df['Close'].ewm(span=26).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9).mean()
    return macd, signal

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

    pred = model.predict(X[-1].reshape(1, -1))[0]
    return pred

# =============================
# ANALYSIS ENGINE
# =============================
def analyze_data(df):
    if df is None or len(df) < 50:
        return None

    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    rsi = calculate_rsi(df)
    macd, signal = calculate_macd(df)
    pred = ai_prediction(df)

    vol = df['Volume']
    avg_vol = vol.rolling(20).mean()

    trend = "CALL STRONG" if df['EMA20'].iloc[-1] > df['EMA50'].iloc[-1] else "PUT STRONG"

    final = "WAIT"

    if (
        df['EMA20'].iloc[-1] > df['EMA50'].iloc[-1] and
        vol.iloc[-1] > avg_vol.iloc[-1] and
        rsi.iloc[-1] < 70 and
        macd.iloc[-1] > signal.iloc[-1] and
        pred and pred > df['Close'].iloc[-1]
    ):
        final = "🚀 ULTRA BUY"

    elif (
        df['EMA20'].iloc[-1] < df['EMA50'].iloc[-1] and
        vol.iloc[-1] > avg_vol.iloc[-1] and
        rsi.iloc[-1] > 30 and
        macd.iloc[-1] < signal.iloc[-1] and
        pred and pred < df['Close'].iloc[-1]
    ):
        final = "💀 ULTRA SELL"

    return trend, final, round(rsi.iloc[-1],2), pred

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

    for i in range(1, len(df)-3):
        prev = df.iloc[i-1]
        curr = df.iloc[i]

        if prev['Close'] <= high and curr['Close'] > high:
            results.append({"Time": df.index[i],"Stock": stock,"Type": "🚀 BUY BO","Level": high})
            break

        elif prev['Close'] >= low and curr['Close'] < low:
            results.append({"Time": df.index[i],"Stock": stock,"Type": "💀 SELL BO","Level": low})
            break

    return results

# =============================
# CHART
# =============================
def plot_chart(df, stock):
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close']
    ))

    fig.add_trace(go.Scatter(x=df.index, y=df['EMA20'], name="EMA20"))
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA50'], name="EMA50"))

    fig.update_layout(title=stock, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

# =============================
# LIVE SCANNER
# =============================
if st.button("🔍 START LIVE SCANNER"):
    results = []
    breakout = []

    for s in stocks:
        try:
            df = yf.Ticker(s + ".NS").history(period="1d", interval="15m")
            df = df.between_time("09:15","15:30")

            if df.empty:
                continue

            res = analyze_data(df)
            bo = breakout_engine(df, s)

            if res:
                trend, signal, rsi, pred = res

                results.append({
                    "Stock": s,
                    "Price": df['Close'].iloc[-1],
                    "Trend": trend,
                    "Signal": signal,
                    "RSI": rsi,
                    "AI Price": round(pred,2) if pred else None
                })

                plot_chart(df, s)

            breakout += bo

        except:
            continue

    st.subheader("📊 LIVE SIGNALS")
    st.dataframe(pd.DataFrame(results), use_container_width=True)

    st.subheader("🔥 BREAKOUT")
    st.dataframe(pd.DataFrame(breakout), use_container_width=True)
