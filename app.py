import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V6", layout="wide")
st_autorefresh(interval=60000, key="refresh")

st.title("🚀 NSE AI PRO DASHBOARD V6")
st.markdown("---")

# =============================
# STOCK LIST
# =============================
stocks = [
    "RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","ITC","LT",
    "AXISBANK","BHARTIARTL","KOTAKBANK","MARUTI","M&M","TATAMOTORS",
    "SUNPHARMA","DRREDDY","CIPLA","HCLTECH","WIPRO","TECHM",
    "JSWSTEEL","TATASTEEL","HINDALCO"
]

# =============================
# SAFE DATA LOADER
# =============================
def get_data(stock):
    try:
        df = yf.Ticker(stock + ".NS").history(period="5d", interval="15m")
        if df is None or df.empty:
            return None
        return df.dropna()
    except:
        return None

# =============================
# AI SCORE
# =============================
def ai_score(df):
    if df is None:
        return 0

    close = df['Close']

    ema20 = close.ewm(span=20).mean()
    ema50 = close.ewm(span=50).mean()

    score = 0

    if ema20.iloc[-1] > ema50.iloc[-1]:
        score += 30
    else:
        score += 10

    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    if rsi.iloc[-1] < 60:
        score += 30
    else:
        score += 10

    if df['Volume'].iloc[-1] > df['Volume'].rolling(20).mean().iloc[-1]:
        score += 40
    else:
        score += 10

    return min(score, 100)

# =============================
# SIGNAL ENGINE
# =============================
def signal(df):
    if df is None:
        return "NO DATA"

    close = df['Close']

    ema20 = close.ewm(span=20).mean()
    ema50 = close.ewm(span=50).mean()

    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    if ema20.iloc[-1] > ema50.iloc[-1] and rsi.iloc[-1] < 65:
        return "🚀 BUY"
    elif ema20.iloc[-1] < ema50.iloc[-1] and rsi.iloc[-1] > 35:
        return "💀 SELL"
    else:
        return "WAIT"

# =============================
# LEVELS
# =============================
def levels(price):
    return price, price*0.98, price*1.03, price*1.06

# =============================
# CHART (FIXED CLARITY)
# =============================
def chart(df, stock):

    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close']
    ))

    fig.update_layout(
        title=f"{stock} CHART",
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)

# =============================
# MAIN DASHBOARD
# =============================
data = []

if st.button("🔍 RUN SCANNER"):

    for s in stocks:
        df = get_data(s)

        if df is None:
            continue

        price = df['Close'].iloc[-1]

        sc = ai_score(df)
        sig = signal(df)

        entry, sl, t1, t2 = levels(price)

        data.append({
            "Stock": s,
            "Price": round(price,2),
            "AI Score": sc,
            "Signal": sig,
            "Entry": round(entry,2),
            "SL": round(sl,2),
            "Target": round(t1,2)
        })

    if len(data) == 0:
        st.error("⚠️ No data found")
    else:
        df = pd.DataFrame(data)

        st.subheader("🏆 TOP 5 STOCKS")
        st.dataframe(df.sort_values("AI Score", ascending=False).head(5), use_container_width=True)

        st.subheader("📊 FULL DASHBOARD")
        st.dataframe(df, use_container_width=True)

# =============================
# CHARTS
# =============================
st.markdown("---")

if st.button("📈 SHOW CHARTS"):

    for s in stocks[:3]:
        df = get_data(s)

        if df is not None:
            chart(df, s)
        else:
            st.warning(f"No data for {s}")

# =============================
# BACKTEST (SAFE)
# =============================
st.markdown("---")

date = st.date_input("📅 Select Date")

def backtest(stock):
    df = yf.Ticker(stock + ".NS").history(period="7d", interval="15m")

    if df is None or df.empty:
        return []

    results = []

    for i in range(20, len(df)):
        sub = df.iloc[:i]

        sig = signal(sub)

        if sig != "WAIT":
            results.append({
                "Stock": stock,
                "Time": sub.index[-1],
                "Signal": sig,
                "Price": sub['Close'].iloc[-1]
            })

    return results

if st.button("📊 RUN BACKTEST"):

    all_res = []

    for s in stocks:
        all_res += backtest(s)

    if len(all_res) == 0:
        st.error("⚠️ No backtest data available")
    else:
        st.subheader("🔥 BACKTEST RESULTS")
        st.dataframe(pd.DataFrame(all_res), use_container_width=True)
