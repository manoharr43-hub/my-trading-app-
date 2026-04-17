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
# STOCK LIST
# =============================
stocks = [
    "RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","ITC","LT",
    "AXISBANK","BHARTIARTL","KOTAKBANK","MARUTI","M&M","TATAMOTORS",
    "SUNPHARMA","DRREDDY","CIPLA","HCLTECH","WIPRO","TECHM",
    "JSWSTEEL","TATASTEEL","HINDALCO"
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
    avg_vol = vol.rolling(20).mean()

    if pd.isna(avg_vol.iloc[-1]) or avg_vol.iloc[-1] == 0:
        return None

    trend = "🔵 CALL STRONG" if e20.iloc[-1] > e50.iloc[-1] else "🔴 PUT STRONG"

    signal = "WAIT"
    if e20.iloc[-1] > e50.iloc[-1] and vol.iloc[-1] > avg_vol.iloc[-1]:
        signal = "🚀 STRONG BUY"
    elif e20.iloc[-1] < e50.iloc[-1] and vol.iloc[-1] > avg_vol.iloc[-1]:
        signal = "💀 STRONG SELL"

    return trend, signal

# =============================
# BACKTEST DATE
# =============================
bt_date = st.sidebar.date_input("📅 Select Backtest Date", datetime.now() - timedelta(days=1))

# =============================
# LIVE SCANNER
# =============================
if st.button("🔍 START LIVE SCANNER (9:15–3:30)"):

    results = []
    breakout_results = []

    for s in stocks:
        try:
            df = yf.Ticker(s + ".NS").history(period="1d", interval="15m")

            if df is None or df.empty:
                continue

            df = df.between_time("09:15","15:30")

            res = analyze_data(df)

            if res:
                results.append({
                    "Stock": s,
                    "Price": df['Close'].iloc[-1],
                    "Trend": res[0],
                    "Signal": res[1],
                    "Time": df.index[-1].strftime("%H:%M")
                })

            # =============================
            # SMART BREAKOUT LIVE
            # =============================
            opening = df.between_time("09:15","09:30")

            if not opening.empty:
                high = opening['High'].max()
                low = opening['Low'].min()

                for i in range(1, len(df)-3):

                    prev = df.iloc[i-1]
                    curr = df.iloc[i]

                    if prev['Close'] <= high and curr['Close'] > high:

                        breakout_results.append({
                            "Time": df.index[i],   # FIXED
                            "Stock": s,
                            "Type": "🚀 CONFIRMED BUY",
                            "Level": round(high,2)
                        })
                        break

                    elif prev['Close'] >= low and curr['Close'] < low:

                        breakout_results.append({
                            "Time": df.index[i],   # FIXED
                            "Stock": s,
                            "Type": "💀 CONFIRMED SELL",
                            "Level": round(low,2)
                        })
                        break

        except:
            continue

    # SORT LIVE BREAKOUT TIME
    breakout_results = sorted(breakout_results, key=lambda x: x["Time"])

    st.subheader("📊 LIVE SIGNALS (9:15–3:30)")
    st.dataframe(pd.DataFrame(results), use_container_width=True)

    st.markdown("---")
    st.subheader("🔥 SMART BREAKOUT STOCKS (TIME ORDER FIXED)")
    st.dataframe(pd.DataFrame(breakout_results), use_container_width=True)

# =============================
# BACKTEST PANEL (FIXED TIME ORDER)
# =============================
st.markdown("---")
st.subheader(f"📅 BACKTEST PANEL - {bt_date}")

if st.button("📊 RUN BACKTEST"):

    bt_signals = []
    bt_breakout = []

    for s in stocks:
        try:
            df = yf.Ticker(s + ".NS").history(
                start=bt_date,
                end=bt_date + timedelta(days=1),
                interval="15m"
            )

            df = df.between_time("09:15","15:30")

            if df.empty:
                continue

            # =============================
            # SIGNAL BACKTEST
            # =============================
            for i in range(20, len(df)):
                sub = df.iloc[:i+1]
                res = analyze_data(sub)

                if res and res[1] != "WAIT":
                    bt_signals.append({
                        "Time": sub.index[-1],
                        "Stock": s,
                        "Signal": res[1]
                    })

            # =============================
            # SMART BREAKOUT BACKTEST (FIXED TIME)
            # =============================
            opening = df.between_time("09:15","09:30")

            if not opening.empty:
                high = opening['High'].max()
                low = opening['Low'].min()

                for i in range(1, len(df)-3):

                    prev = df.iloc[i-1]
                    curr = df.iloc[i]

                    if prev['Close'] <= high and curr['Close'] > high:

                        bt_breakout.append({
                            "Time": df.index[i],   # FIXED
                            "Stock": s,
                            "Type": "🚀 BUY BREAKOUT",
                            "Level": round(high,2)
                        })
                        break

                    elif prev['Close'] >= low and curr['Close'] < low:

                        bt_breakout.append({
                            "Time": df.index[i],   # FIXED
                            "Stock": s,
                            "Type": "💀 SELL BREAKOUT",
                            "Level": round(low,2)
                        })
                        break

        except:
            continue

    # =============================
    # FINAL SORT (VERY IMPORTANT)
    # =============================
    bt_breakout = sorted(bt_breakout, key=lambda x: x["Time"])
    bt_signals = sorted(bt_signals, key=lambda x: x["Time"])

    # FORMAT TIME CLEAN
    for x in bt_breakout:
        x["Time"] = pd.to_datetime(x["Time"]).strftime("%H:%M")

    for x in bt_signals:
        x["Time"] = pd.to_datetime(x["Time"]).strftime("%H:%M")

    st.subheader("📊 BACKTEST SIGNALS (TIME ORDER FIXED)")
    st.dataframe(pd.DataFrame(bt_signals), use_container_width=True)

    st.markdown("---")
    st.subheader("🔥 BACKTEST SMART BREAKOUT (9:15–3:30 ORDER)")
    st.dataframe(pd.DataFrame(bt_breakout), use_container_width=True)
