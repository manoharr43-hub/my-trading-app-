import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 MANOHAR NSE AI PRO", layout="wide")
st_autorefresh(interval=60000, key="refresh")

st.title("🚀 MANOHAR NSE AI PRO TERMINAL")
st.markdown("---")

# =============================
# NSE STOCK LIST (FULL CORE)
# =============================
stocks = [
    "RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","ITC","LT",
    "AXISBANK","BHARTIARTL","KOTAKBANK","MARUTI","M&M","TATAMOTORS",
    "SUNPHARMA","DRREDDY","CIPLA","HCLTECH","WIPRO","TECHM",
    "JSWSTEEL","TATASTEEL","HINDALCO","POWERGRID","NTPC"
]

# =============================
# ANALYSIS ENGINE
# =============================
def analyze_data(df):
    if df is None or len(df) < 20:
        return None

    e20 = df['Close'].ewm(span=20).mean()
    e50 = df['Close'].ewm(span=50).mean()

    vol = df['Volume']
    avg_vol = vol.rolling(window=20).mean()

    curr_price = df['Close'].iloc[-1]
    curr_e20 = e20.iloc[-1]
    curr_e50 = e50.iloc[-1]
    curr_vol = vol.iloc[-1]
    curr_avg_vol = avg_vol.iloc[-1]

    if pd.isna(curr_avg_vol) or curr_avg_vol == 0:
        return None

    trend = "🔵 CALL STRONG" if curr_e20 > curr_e50 else "🔴 PUT STRONG"

    if curr_vol > curr_avg_vol * 2:
        big_player = "🔥 EXTREME INSTITUTIONAL"
    elif curr_vol > curr_avg_vol * 1.5:
        big_player = "🐋 BIG PLAYER ACTIVE"
    else:
        big_player = "💤 NORMAL"

    signal = "WAIT"
    entry, sl, target = 0, 0, 0

    recent_high = df['High'].iloc[-10:].max()
    recent_low = df['Low'].iloc[-10:].min()
    risk = (recent_high - recent_low) if (recent_high - recent_low) > 0 else curr_price * 0.01

    if curr_e20 > curr_e50 and curr_vol > curr_avg_vol:
        signal = "🚀 STRONG BUY"
        entry = curr_price
        sl = curr_price - risk * 0.5
        target = curr_price + risk

    elif curr_e20 < curr_e50 and curr_vol > curr_avg_vol:
        signal = "💀 STRONG SELL"
        entry = curr_price
        sl = curr_price + risk * 0.5
        target = curr_price - risk

    return trend, signal, big_player, round(entry,2), round(sl,2), round(target,2)

# =============================
# LIVE SCANNER
# =============================
if st.button("🔍 START LIVE SCANNER (9:15 - 3:30)", use_container_width=True):

    results = []
    breakout = []

    with st.spinner("Scanning NSE Market..."):

        for s in stocks:
            try:
                df = yf.Ticker(s + ".NS").history(period="1d", interval="15m")

                if df is None or df.empty:
                    continue

                # TIME FILTER
                df = df.between_time("09:15", "15:30")

                res = analyze_data(df)

                if res:
                    results.append({
                        "Stock": s,
                        "Price": round(df['Close'].iloc[-1],2),
                        "Trend": res[0],
                        "Signal": res[1],
                        "Big Player": res[2],
                        "Entry": res[3],
                        "SL": res[4],
                        "Target": res[5],
                        "Time": df.index[-1].strftime("%H:%M")
                    })

                # =============================
                # SMART BREAKOUT
                # =============================
                opening = df.between_time("09:15","09:30")

                if not opening.empty:
                    high = opening['High'].max()
                    low = opening['Low'].min()

                    for i in range(1, len(df)-3):

                        prev = df.iloc[i-1]
                        curr = df.iloc[i]
                        time = df.index[i]

                        if prev['Close'] <= high and curr['Close'] > high:

                            future = df.iloc[i+1:i+4]
                            up = sum(future['Close'] > curr['Close'])
                            down = sum(future['Close'] <= curr['Close'])

                            breakout.append({
                                "Stock": s,
                                "Type": "🚀 CONFIRMED BUY" if up > down else "⚠️ FAILED BUY",
                                "Level": round(high,2),
                                "Time": time.strftime("%H:%M")
                            })
                            break

                        elif prev['Close'] >= low and curr['Close'] < low:

                            future = df.iloc[i+1:i+4]
                            down = sum(future['Close'] < curr['Close'])
                            up = sum(future['Close'] >= curr['Close'])

                            breakout.append({
                                "Stock": s,
                                "Type": "💀 CONFIRMED SELL" if down > up else "⚠️ FAILED SELL",
                                "Level": round(low,2),
                                "Time": time.strftime("%H:%M")
                            })
                            break

            except:
                continue

    st.subheader("📊 LIVE NSE AI RESULTS (9:15–3:30)")
    st.dataframe(pd.DataFrame(results), use_container_width=True)

    st.markdown("---")
    st.subheader("🔥 SMART BREAKOUT STOCKS (ALL NSE)")
    st.dataframe(pd.DataFrame(breakout), use_container_width=True)

# =============================
# BACKTEST PANEL
# =============================
st.markdown("---")
st.subheader("📅 BACKTEST PANEL (9:15–3:30 ONLY)")

if st.button("📊 RUN BACKTEST"):

    bt_results = []

    with st.spinner("Running Backtest..."):

        for s in stocks:
            try:
                df = yf.Ticker(s + ".NS").history(
                    start=datetime.now() - timedelta(days=7),
                    end=datetime.now(),
                    interval="15m"
                )

                df = df.between_time("09:15","15:30")

                for i in range(20, len(df)):
                    sub = df.iloc[:i+1]
                    res = analyze_data(sub)

                    if res and res[1] != "WAIT":
                        bt_results.append({
                            "Time": sub.index[-1].strftime("%H:%M"),
                            "Stock": s,
                            "Signal": res[1],
                            "Entry": res[3],
                            "SL": res[4],
                            "Target": res[5]
                        })

            except:
                continue

    st.dataframe(pd.DataFrame(bt_results), use_container_width=True)
