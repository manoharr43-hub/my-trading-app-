import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# =============================
# 1. CONFIG
# =============================
st.set_page_config(page_title="🔥 MANOHAR NSE AI PRO", layout="wide")
st_autorefresh(interval=60000, key="refresh")

st.title("🚀 MANOHAR NSE AI PRO TERMINAL")
st.markdown("---")

# =============================
# 2. RSI CALCULATION
# =============================
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# =============================
# 3. SuperTrend Calculation
# =============================
def calculate_supertrend(df, period=10, multiplier=3):
    hl2 = (df['High'] + df['Low']) / 2
    atr = df['High'].rolling(period).max() - df['Low'].rolling(period).min()
    upperband = hl2 + (multiplier * atr)
    lowerband = hl2 - (multiplier * atr)
    supertrend = pd.Series(index=df.index, dtype=float)
    for i in range(len(df)):
        if df['Close'].iloc[i] > upperband.iloc[i]:
            supertrend.iloc[i] = 1
        elif df['Close'].iloc[i] < lowerband.iloc[i]:
            supertrend.iloc[i] = -1
        else:
            supertrend.iloc[i] = 0
    return supertrend

# =============================
# 4. Bollinger Bands Calculation
# =============================
def calculate_bollinger(df, period=20):
    sma = df['Close'].rolling(window=period).mean()
    std = df['Close'].rolling(window=period).std()
    upper = sma + (2 * std)
    lower = sma - (2 * std)
    return sma, upper, lower

# =============================
# 5. ANALYSIS LOGIC
# =============================
def analyze_data(df):
    if df is None or len(df) < 20:
        return None

    e20 = df['Close'].ewm(span=20).mean()
    e50 = df['Close'].ewm(span=50).mean()

    rsi_series = calculate_rsi(df['Close'])
    rsi = rsi_series.iloc[-1]
    if pd.isna(rsi):
        return None

    st_signal = calculate_supertrend(df)
    st_last = st_signal.iloc[-1]

    sma, upper, lower = calculate_bollinger(df)
    bb_upper, bb_lower = upper.iloc[-1], lower.iloc[-1]

    vol = df['Volume']
    avg_vol = vol.rolling(window=20).mean()

    curr_price = df['Close'].iloc[-1]
    curr_e20, curr_e50 = e20.iloc[-1], e50.iloc[-1]
    curr_vol, curr_avg_vol = vol.iloc[-1], avg_vol.iloc[-1]

    last_candle = df.iloc[-1]
    candle_signal = "Bullish" if last_candle['Close'] > last_candle['Open'] else "Bearish"

    cp_strength = "🔵 CALL STRONG" if curr_e20 > curr_e50 else "🔴 PUT STRONG"
    if curr_vol > curr_avg_vol * 2:
        big_player = "🔥 EXTREME INSTITUTIONAL"
    elif curr_vol > curr_avg_vol * 1.5:
        big_player = "🐋 BIG PLAYER ACTIVE"
    else:
        big_player = "💤 NORMAL"

    recent_high = df['High'].iloc[-10:].max()
    recent_low = df['Low'].iloc[-10:].min()
    risk = (recent_high - recent_low) if (recent_high - recent_low) > 0 else curr_price * 0.01

    observation, entry, sl, target = "WAIT", 0, 0, 0
    if (curr_e20 > curr_e50 and curr_vol > curr_avg_vol and candle_signal == "Bullish"
        and rsi > 45 and st_last == 1 and curr_price > bb_upper):
        observation = "🚀 STRONG BUY"
        entry = curr_price
        sl = curr_price - (risk * 0.5)
        target = curr_price + risk
    elif (curr_e20 < curr_e50 and curr_vol > curr_avg_vol and candle_signal == "Bearish"
          and rsi < 55 and st_last == -1 and curr_price < bb_lower):
        observation = "💀 STRONG SELL"
        entry = curr_price
        sl = curr_price + (risk * 0.5)
        target = curr_price - risk

    return (cp_strength, observation, big_player, round(entry,2), round(sl,2), round(target,2), round(rsi,2))

# =============================
# 6. NSE SECTORS (Expanded)
# =============================
all_sectors = {
    "Nifty 50": ["RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","ITC","LT","AXISBANK","BHARTIARTL"],
    "Banking": ["HDFCBANK","ICICIBANK","AXISBANK","KOTAKBANK","SBIN","PNB","BANKBARODA"],
    "IT": ["TCS","INFY","WIPRO","HCLTECH","TECHM"],
    "Pharma": ["SUNPHARMA","DRREDDY","CIPLA","DIVISLAB","APOLLOHOSP"],
    "FMCG": ["ITC","HINDUNILVR","NESTLEIND","BRITANNIA","DABUR"],
    "Auto": ["TATAMOTORS","M&M","MARUTI","HEROMOTOCO","BAJAJ-AUTO"],
    "Metal": ["TATASTEEL","JSWSTEEL","HINDALCO","VEDL","NMDC"],
    "Energy": ["RELIANCE","ONGC","NTPC","POWERGRID","BPCL","IOC"],
    "Realty": ["DLF","GODREJPROP","OBEROIRLTY","PHOENIXLTD"],
    "Media": ["ZEEL","SUNTV","PVRINOX"],
    "PSU Banks": ["SBIN","PNB","BANKBARODA","CANBK","UNIONBANK"]
}

# =============================
# 7. SIDEBAR
# =============================
st.sidebar.title("📂 Backtest Panel")
bt_date = st.sidebar.date_input("Select Date", datetime.now() - timedelta(days=1))
bt_stock_input = st.sidebar.text_input("Stock (optional)", "").upper()

# =============================
# 8. MAIN SCANNER
# =============================
selected_sector = st.selectbox("📂 Select Sector", list(all_sectors.keys()))
stocks = all_sectors[selected_sector]

if st.button("🔍 START LIVE SCANNER", use_container_width=True):
    results = []
    with st.spinner("AI Scanning Market..."):
        for s in stocks:
            try:
                t = yf.Ticker(s + ".NS")
                df = t.history(period="2d", interval="15m")
                res = analyze_data(df)
                if res:
                    results.append({
                        "Stock": s,
                        "Price": round(df['Close'].iloc[-1], 2),
                        "Trend": res[0],
                        "Signal": res[1],
                        "Big Player": res[2],
                        "Entry": res[3],
                        "SL": res[4],
                        "Target": res[5],
                        "RSI": res[6],
                        "Time": df.index[-1].strftime('%H:%M')
                    })
            except:
                continue
    st.dataframe(pd.DataFrame(results), use_container_width=True)

# =============================
# 9. BACKTEST (FULL DAY FIX)
# =============================
st.markdown("---")
st.subheader(f"📅 Backtest Report - {bt_date}")

if st.sidebar.button("📊 RUN BACKTEST"):
    bt_results = []
    target_list = [bt_stock_input] if bt_stock_input else stocks
    with st.spinner("Running Backtest..."):
        for s in target_list:
            try:
                t = yf.Ticker(s + ".NS")
                df_hist = t.history(start=bt_date, end=bt_date + timedelta(days=1), interval="15m")
                if not df_hist.empty:
                    for i in range(5, len(df_hist)):   # ✅ full-day signals
                        sub_df = df_hist.iloc[:i+1]
                        res = analyze
