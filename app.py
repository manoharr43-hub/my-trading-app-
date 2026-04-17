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
# NSE STOCK LIST
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

    trend = "CALL STRONG" if e20.iloc[-1] > e50.iloc[-1] else "PUT STRONG"

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

    live_results = []
    live_breakout = []

    for s in stocks:
        try:
            df = yf.Ticker(s + ".NS").history(period="1d", interval="15m")

            if df.empty:
                continue

            df = df.between_time("09:15", "15:30")

            res = analyze_data(df)

            if res:
                live_results.append({
                    "Stock": s,
                    "Price": df['Close'].iloc[-1],
                    "Trend": res[0],
                    "Signal": res[1],
                    "Time": df.index[-1].strftime("%H:%M")
                })

            # =============================
            # SMART BREAKOUT LIVE
            # =============================
            opening = df.between_time("09:15", "09:30")

            if not opening.empty:
                high = opening['High'].max()
                low = opening['Low'].min()

                for i in range(1, len(df)-3):

                    prev = df.iloc[i-1]
                    curr = df.iloc[i]
                    t = df.index[i]

                    if prev['Close'] <= high and curr['Close'] > high:

                        live_breakout.append({
                            "Time": t,
                            "Stock": s,
                            "Type": "🚀 BUY BREAKOUT",
                            "Level": round(high,2)
                        })
                        break

                    elif prev['Close'] >= low and curr['Close'] < low:

                        live_breakout.append({
                            "Time": t,
                            "Stock": s,
                            "Type": "💀 SELL BREAKOUT",
                            "Level": round(low,2)
                        })
                        break

        except:
            continue

    # SORT LIVE BREAKOUT
    live_breakout = sorted(live_breakout, key=lambda x: x["Time"])

    for x in live_breakout:
        x["Time"] = pd.to_datetime(x["Time"]).strftime("%H:%M")

    st.subheader("📊 LIVE SIGNALS (9:15–3:30)")
    st.dataframe(pd.DataFrame(live_results), use_container_width=True)

    st.markdown("---")
    st.subheader("🔥 SMART BREAKOUT STOCKS (TIME ORDER FIXED)")
    st.dataframe(pd.DataFrame(live_breakout), use_container_width=True)

# =============================
# BACKTEST PANEL (FULL FIXED)
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

            df = df.between_time("09:15", "15:30")

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
            # SMART BREAKOUT BACKTEST
            # =============================
            opening = df.between_time("09:15", "09:30")

            if not opening.empty:
                high = opening['High'].max()
                low = opening['Low'].min()

                for i in range(1, len(df)-3):

                    prev = df.iloc[i-1]
                    curr = df.iloc[i]
                    t = df.index[i]

                    if prev['Close'] <= high and curr['Close'] > high:

                        bt_breakout.append({
                            "Time": t,
                            "Stock": s,
                            "Type": "🚀 BUY BREAKOUT",
                            "Level": round(high,2)
                        })
                        break

                    elif prev['Close'] >= low and curr['Close'] < low:

                        bt_breakout.append({
                            "Time": t,
                            "Stock": s,
                            "Type": "💀 SELL BREAKOUT",
                            "Level": round(low,2)
                        })
                        break

        except:
            continue

    # =============================
    # FINAL SORT FIX (IMPORTANT)
    # =============================
    bt_breakout = sorted(bt_breakout, key=lambda x: x["Time"])
    bt_signals = sorted(bt_signals, key=lambda x: x["Time"])

    for x in bt_breakout:
        x["Time"] = pd.to_datetime(x["Time"]).strftime("%H:%M")

    for x in bt_signals:
        x["Time"] = pd.to_datetime(x["Time"]).strftime("%H:%M")

    st.subheader("📊 BACKTEST SIGNALS (ORDER FIXED)")
    st.dataframe(pd.DataFrame(bt_signals), use_container_width=True)

    st.markdown("---")
    st.subheader("🔥 SMART BREAKOUT BACKTEST (9:15–3:30 ORDER)")
    st.dataframe(pd.DataFrame(bt_breakout), use_container_width=True)
