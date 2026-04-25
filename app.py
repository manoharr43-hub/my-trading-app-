import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from streamlit_autorefresh import st_autorefresh
import plotly.graph_objects as go

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V9", layout="wide")
st_autorefresh(interval=60000, key="refresh")

st.title("🚀 NSE AI PRO V9 - SECTOR + BACKTEST FIXED")

# =============================
# SESSION
# =============================
if "bt_history" not in st.session_state:
    st.session_state.bt_history = []

# =============================
# SECTORS
# =============================
sector_map = {
    "Banking": ["HDFCBANK","ICICIBANK","SBIN","AXISBANK","KOTAKBANK"],
    "IT": ["TCS","INFY","HCLTECH","WIPRO","TECHM"],
    "Auto": ["MARUTI","M&M","TATAMOTORS"],
    "FMCG": ["ITC","HINDUNILVR","NESTLEIND"],
    "Energy": ["RELIANCE","ONGC","NTPC"]
}

all_stocks = list(set(sum(sector_map.values(), [])))

# =============================
# DATA
# =============================
@st.cache_data(ttl=300)
def load_data(stock):
    return yf.Ticker(stock + ".NS").history(period="5d", interval="5m")

# =============================
# RSI
# =============================
def rsi(df):
    delta = df['Close'].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / (loss + 1e-10)
    return 100 - (100 / (1 + rs))

# =============================
# ANALYSIS
# =============================
def analyze(df):

    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    r = rsi(df).iloc[-1]

    vol_ok = df['Volume'].iloc[-1] > df['Volume'].rolling(20).mean().iloc[-1]

    up = df['EMA20'].iloc[-1] > df['EMA50'].iloc[-1]
    down = df['EMA20'].iloc[-1] < df['EMA50'].iloc[-1]

    score = 0

    if up:
        score += 2
    if vol_ok:
        score += 1
    if r < 70:
        score += 1

    sell_score = 0

    if down:
        sell_score += 2
    if vol_ok:
        sell_score += 1
    if r > 30:
        sell_score += 1

    return score, sell_score

# =============================
# ENTRY SYSTEM
# =============================
def entry_system(df):
    price = df['Close'].iloc[-1]
    atr = (df['High'] - df['Low']).rolling(14).mean().iloc[-1]

    return round(price - atr*1.5,2), round(price + atr*3,2)

# =============================
# SECTOR SCANNER
# =============================
st.subheader("📡 NSE SECTOR SCANNER")

buy_list = []
sell_list = []

for sector, stocks in sector_map.items():

    st.markdown(f"### 🔹 {sector}")

    table = []

    for s in stocks:

        df = load_data(s)

        if df is None or len(df) < 50:
            continue

        buy_score, sell_score = analyze(df)
        sl, tgt = entry_system(df)

        table.append({
            "Stock": s,
            "BUY_SCORE": buy_score,
            "SELL_SCORE": sell_score,
            "SL": sl,
            "TARGET": tgt
        })

    df_sector = pd.DataFrame(table)

    st.dataframe(df_sector)

# =============================
# TOP 5 BUY / SELL STRONG
# =============================
st.subheader("🔥 TOP 5 BUY / SELL STRONG")

score_table = []

for s in all_stocks:

    df = load_data(s)

    if df is None or len(df) < 50:
        continue

    buy_score, sell_score = analyze(df)

    score_table.append({
        "Stock": s,
        "BUY_SCORE": buy_score,
        "SELL_SCORE": sell_score
    })

df_score = pd.DataFrame(score_table)

top_buy = df_score.sort_values("BUY_SCORE", ascending=False).head(5)
top_sell = df_score.sort_values("SELL_SCORE", ascending=False).head(5)

col1, col2 = st.columns(2)

with col1:
    st.success("🚀 TOP 5 BUY STRONG")
    st.dataframe(top_buy)

with col2:
    st.error("💀 TOP 5 SELL STRONG")
    st.dataframe(top_sell)

# =============================
# BACKTEST FIXED
# =============================
st.subheader("📊 BACKTEST FIXED")

bt_days = st.slider("Backtest Days", 1, 10, 5)

if st.button("RUN BACKTEST"):

    results = []

    for s in all_stocks:

        df = yf.Ticker(s + ".NS").history(period=f"{bt_days}d", interval="5m")

        if df is None or len(df) < 50:
            continue

        buy_score, sell_score = analyze(df)
        sl, tgt = entry_system(df)

        results.append({
            "Stock": s,
            "BUY_SCORE": buy_score,
            "SELL_SCORE": sell_score,
            "SL": sl,
            "TARGET": tgt
        })

    res_df = pd.DataFrame(results)

    st.session_state.bt_history.append(res_df)

    st.success("✅ BACKTEST DONE")
    st.dataframe(res_df)

# =============================
# BACKTEST HISTORY
# =============================
st.subheader("📁 BACKTEST HISTORY")

if st.session_state.bt_history:

    for i, df in enumerate(st.session_state.bt_history[::-1]):

        with st.expander(f"Run #{i+1}"):
            st.dataframe(df)

else:
    st.info("No backtest yet")
