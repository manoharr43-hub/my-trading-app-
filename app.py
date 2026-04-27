import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
from io import BytesIO
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V12", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V12 - PULLBACK ENTRY SYSTEM")
st.write(f"🕒 {now.strftime('%Y-%m-%d %H:%M:%S')}")
st.markdown("---")

# =============================
# STOCKS
# =============================
stocks = [
    "RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK",
    "SBIN","ITC","LT","BHARTIARTL","AXISBANK",
    "KOTAKBANK","HCLTECH","WIPRO","MARUTI","ASIANPAINT"
]

# =============================
# DATA
# =============================
@st.cache_data(ttl=300)
def get_data(symbol, interval="5m", period="5d"):
    try:
        df = yf.Ticker(symbol + ".NS").history(period=period, interval=interval)
        if df is None or df.empty:
            return None

        if df.index.tz is None:
            df.index = df.index.tz_localize("UTC").tz_convert(IST)
        else:
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

    df['ATR'] = (df['High'] - df['Low']).rolling(14).mean()

    return df

# =============================
# AI SCORE
# =============================
def ai_score(df):
    last = df.iloc[-1]
    score = 0

    if last['EMA20'] > last['EMA50']: score += 25
    if 50 < last['RSI'] < 70: score += 15
    if last['Close'] > last['VWAP']: score += 20
    if last['MACD'] > last['Signal']: score += 20
    if last['Volume'] > df['Volume'].rolling(20).mean().iloc[-1]: score += 20

    return score

# =============================
# SIGNAL
# =============================
def signal(score):
    if score >= 80: return "🚀 STRONG BUY"
    elif score >= 60: return "BUY"
    elif score <= 20: return "💀 STRONG SELL"
    elif score <= 40: return "SELL"
    else: return "WAIT"

# =============================
# SMART MONEY
# =============================
def smart_money(df):
    last = df.iloc[-1]
    avg_vol = df['Volume'].rolling(20).mean().iloc[-1]

    move = abs(last['Close'] - last['Open']) / last['Open'] * 100

    if last['Volume'] > avg_vol * 2 and move > 0.5:
        if last['Close'] > last['VWAP']:
            return "🔥 BIG BUYER"
        else:
            return "💀 BIG SELLER"
    return ""

# =============================
# PULLBACK ENTRY
# =============================
def pullback_entry(df):
    try:
        last = df.iloc[-1]

        breakout = last['Close'] > df['High'].rolling(20).max().iloc[-2]

        pullback = abs(last['Close'] - last['EMA20']) / last['EMA20'] < 0.004

        bullish = last['Close'] > last['Open']

        volume_ok = last['Volume'] > df['Volume'].rolling(20).mean().iloc[-1]

        if breakout and pullback and bullish and volume_ok:
            return "✅ PULLBACK ENTRY"
        else:
            return ""
    except:
        return ""

# =============================
# EXCEL
# =============================
def convert_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

# =============================
# TABS
# =============================
tab1, tab2 = st.tabs(["🔍 LIVE SCANNER", "📊 BACKTEST"])

# =============================
# LIVE SCANNER
# =============================
with tab1:

    if st.button("🚀 RUN SCAN"):

        results = []

        for s in stocks:

            df5 = get_data(s, "5m")
            df15 = get_data(s, "15m")
            df1h = get_data(s, "1h")

            if any(x is None or x.empty for x in [df5, df15, df1h]):
                continue

            df5 = add_indicators(df5)
            df15 = add_indicators(df15)
            df1h = add_indicators(df1h)

            score = (ai_score(df5) + ai_score(df15) + ai_score(df1h)) / 3
            sig = signal(score)

            pb = pullback_entry(df5)

            if "STRONG" not in sig:
                continue

            price = df5['Close'].iloc[-1]
            atr = df5['ATR'].iloc[-1]

            entry = round(price, 2)
            target = round(entry + atr * 1.5, 2)
            sl = round(entry - atr, 2)

            results.append({
                "STOCK": s,
                "PRICE": entry,
                "SIGNAL": sig,
                "PULLBACK": pb,
                "SMART": smart_money(df5),
                "TARGET": target,
                "SL": sl,
                "SCORE": round(score,1)
            })

        if results:
            df = pd.DataFrame(results).sort_values("SCORE", ascending=False)
            st.dataframe(df, use_container_width=True)
            st.success(f"{len(df)} Signals Found")
        else:
            st.warning("No signals")

# =============================
# BACKTEST
# =============================
with tab2:

    date = st.date_input("📅 Select Date")

    if st.button("📈 RUN BACKTEST"):

        logs = []
        wins = 0
        total = 0

        for s in stocks:

            df = get_data(s, "5m", "7d")

            if df is None or df.empty:
                continue

            df = add_indicators(df)
            df = df[df.index.date == date]
            df = df.between_time("09:15", "15:30")

            if len(df) < 30:
                continue

            for i in range(20, len(df)-1):

                temp = df.iloc[:i+1]

                sc = ai_score(temp)
                sig = signal(sc)

                entry = temp.iloc[-1]['Close']
                next_p = df.iloc[i+1]['Close']

                if sig in ["BUY", "🚀 STRONG BUY"]:
                    res = "WIN" if next_p > entry else "LOSS"

                elif sig in ["SELL", "💀 STRONG SELL"]:
                    res = "WIN" if next_p < entry else "LOSS"

                else:
                    continue

                if res == "WIN":
                    wins += 1

                total += 1

                logs.append({
                    "TIME": df.index[i].strftime('%H:%M'),
                    "STOCK": s,
                    "SIGNAL": sig,
                    "ENTRY": round(entry,2),
                    "NEXT": round(next_p,2),
                    "RESULT": res
                })

        if logs:
            df_logs = pd.DataFrame(logs)
            acc = (wins/total)*100 if total > 0 else 0

            st.dataframe(df_logs, use_container_width=True)
            st.metric("🎯 Accuracy", f"{acc:.2f}%")
            st.success(f"Total Trades: {total}")

            excel = convert_excel(df_logs)
            st.download_button("📥 Download Excel", excel, "backtest.xlsx")

        else:
            st.warning("No trades found")

# =============================
# CHART
# =============================
st.markdown("---")

stock_sel = st.selectbox("📊 Chart View", stocks)
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
